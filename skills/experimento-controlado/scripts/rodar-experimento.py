#!/usr/bin/env python3
# Caminho relativo: skills/experimento-controlado/scripts/rodar-experimento.py
#
# Roda um experimento controlado de instrução (prompt, regra, skill): cada caso, em cada braço,
# repetido N vezes, em ordem embaralhada, corrigido sem que o corretor saiba o braço. Imprime a
# taxa de acerto por braço com intervalo de Wilson a 95% e diz se os intervalos se separam.
#
#   rodar-experimento.py docs/experimentos/EXP-0001-x/experimento.json
#   rodar-experimento.py <manifesto> --repeticoes 1 --casos divergencia   # ensaio de fumaça
#   rodar-experimento.py --autoteste
#
# Backend: qualquer executável com a interface do `oa-chat` (skill delegacao-openai-compat):
#   <backend> [-s SISTEMA] -m MODELO -t TEMPERATURA --max-tokens N -f PEDIDO
# conteúdo em stdout, código 0 = ok. A credencial é do backend; este script nunca a vê.
#
# Erro de backend NÃO conta como falha do braço: vai para uma coluna própria, e acima de 10%
# das chamadas o resultado é declarado inválido. Falha de rede lida como "o tratamento errou"
# é exatamente o tipo de conclusão que este script existe para impedir.
#
# Códigos: 0 rodou · 1 resultado inválido (erros demais) · 2 uso/manifesto · 3 autoteste falhou
import argparse
import concurrent.futures as cf
import hashlib
import json
import math
import os
import random
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

AQUI = Path(__file__).resolve().parent
# Instalado, as skills ficam lado a lado; no repositório também. O mesmo caminho serve aos dois.
BACKEND_PADRAO = AQUI.parents[1] / "delegacao-openai-compat" / "scripts" / "oa-chat"
CAMPOS_OBRIGATORIOS = ("id", "hipotese", "criterio_de_refutacao", "bracos", "casos")
TETO_DE_ERROS = 0.10
# Controle e tratamento com tamanhos muito diferentes deixam de isolar o conteúdo: o efeito
# pode ser de "mais texto no sistema", que é a confusão que o controle existe para desfazer.
TOLERANCIA_DE_TAMANHO = 0.25


def falhar(msg, codigo=2):
    print(f"rodar-experimento: {msg}", file=sys.stderr)
    sys.exit(codigo)


def wilson(acertos, n, z=1.96):
    """Intervalo de Wilson a 95%. Com n pequeno, o intervalo normal sai de [0, 1]; este não."""
    if n == 0:
        return (0.0, 1.0)
    p = acertos / n
    den = 1 + z * z / n
    centro = (p + z * z / (2 * n)) / den
    meia = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return (max(0.0, centro - meia), min(1.0, centro + meia))


def carregar(manifesto_path, so_casos=None):
    try:
        m = json.loads(manifesto_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as e:
        falhar(f"manifesto ilegível: {manifesto_path}: {e}")
    faltam = [c for c in CAMPOS_OBRIGATORIOS if not m.get(c)]
    if faltam:
        # Sem critério de refutação escrito ANTES, qualquer resultado vira confirmação.
        falhar(f"manifesto sem campo obrigatório: {', '.join(faltam)}")
    base = manifesto_path.parent
    bracos = {}
    for nome, arq in m["bracos"].items():
        if arq is None:
            bracos[nome] = None  # braço sem prompt de sistema: o modelo como vem
        else:
            p = base / arq
            if not p.is_file():
                falhar(f"braço '{nome}': arquivo ausente: {p}")
            bracos[nome] = p.read_text(encoding="utf-8")
    casos = []
    for c in m["casos"]:
        if so_casos and c["id"] not in so_casos:
            continue
        p = base / c["pedido"]
        if not p.is_file():
            falhar(f"caso '{c['id']}': pedido ausente: {p}")
        caso = dict(c, pedido_texto=p.read_text(encoding="utf-8"))
        if c.get("rubrica"):
            r = base / c["rubrica"]
            if not r.is_file():
                falhar(f"caso '{c['id']}': rubrica ausente: {r}")
            caso["rubrica_texto"] = r.read_text(encoding="utf-8")
        if not (c.get("deve_conter") or c.get("nao_deve_conter") or c.get("rubrica")):
            falhar(f"caso '{c['id']}': sem correção (deve_conter, nao_deve_conter ou rubrica)")
        casos.append(caso)
    if not casos:
        falhar("nenhum caso selecionado")
    return m, bracos, casos


def pre_registro(manifesto_path):
    """'sim (<commit>)' se o manifesto está versionado e sem alteração; senão, exploratório.

    Só lê o git. Critério alterado depois de ver resultado é o que transforma experimento em
    narrativa — o commit é a data que prova que o critério veio antes.
    """
    d = str(manifesto_path.parent)
    try:
        sujo = subprocess.run(["git", "-C", d, "status", "--porcelain", "--", manifesto_path.name],
                              capture_output=True, text=True, timeout=30)
        if sujo.returncode != 0:
            return "não — fora de repositório git: exploratório"
        if sujo.stdout.strip():
            return "não — manifesto alterado ou não versionado: exploratório"
        c = subprocess.run(["git", "-C", d, "log", "-1", "--format=%h %cs", "--", manifesto_path.name],
                           capture_output=True, text=True, timeout=30)
        return f"sim ({c.stdout.strip()})" if c.stdout.strip() else "não — sem commit: exploratório"
    except (OSError, subprocess.TimeoutExpired):
        return "não — git indisponível: exploratório"


def chamar(backend, sistema, pedido, modelo, temperatura, max_tokens, timeout, extras=()):
    with tempfile.NamedTemporaryFile("w", suffix=".md", delete=False, encoding="utf-8") as f:
        f.write(pedido)
        arq = f.name
    try:
        cmd = [str(backend), *extras]
        if sistema:
            cmd += ["-s", sistema]
        if modelo:
            cmd += ["-m", modelo]
        cmd += ["-t", str(temperatura), "--max-tokens", str(max_tokens), "-f", arq]
        t0 = time.monotonic()
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        dt = round(time.monotonic() - t0, 2)
        if r.returncode != 0:
            return None, f"backend saiu {r.returncode}: {r.stderr.strip()[-300:]}", dt
        return r.stdout, None, dt
    except subprocess.TimeoutExpired:
        return None, f"timeout de {timeout}s", timeout
    except OSError as e:
        return None, f"backend não executou: {e}", 0
    finally:
        os.unlink(arq)


def corrigir_regex(caso, resposta):
    for rx in caso.get("deve_conter", []):
        if not re.search(rx, resposta, re.I | re.M):
            return False, f"faltou /{rx}/"
    for rx in caso.get("nao_deve_conter", []):
        if re.search(rx, resposta, re.I | re.M):
            return False, f"apareceu /{rx}/"
    return True, "regex ok"


def corrigir_juiz(caso, resposta, backend, juiz, timeout):
    """O juiz vê o pedido e a resposta, nunca o braço. Primeira linha: PASSA ou FALHA."""
    pedido = (f"## Pedido feito ao modelo avaliado\n\n{caso['pedido_texto']}\n\n"
              f"## Resposta do modelo avaliado\n\n{resposta}\n\n"
              "Responda na PRIMEIRA linha apenas PASSA ou FALHA. Na segunda, o motivo em uma frase.")
    saida, erro, _ = chamar(backend, caso["rubrica_texto"], pedido, juiz.get("modelo"),
                            juiz.get("temperatura", 0), juiz.get("max_tokens", 2000), timeout,
                            juiz.get("argumentos_backend", []))
    if erro:
        return None, f"juiz: {erro}"
    linhas = [l.strip() for l in saida.strip().splitlines() if l.strip()]
    primeira = re.sub(r"[^A-Z]", "", linhas[0].upper()) if linhas else ""
    motivo = linhas[1] if len(linhas) > 1 else ""
    if primeira == "PASSA":
        return True, f"juiz: {motivo}"
    if primeira == "FALHA":
        return False, f"juiz: {motivo}"
    return None, f"juiz fora do formato: {saida.strip()[:120]!r}"


def executar(manifesto_path, args):
    m, bracos, casos = carregar(manifesto_path, args.casos)
    backend = Path(args.backend or os.environ.get("EXPERIMENTO_BACKEND") or BACKEND_PADRAO)
    if not os.access(backend, os.X_OK):
        falhar(f"backend não executável: {backend}")
    reps = args.repeticoes or int(m.get("repeticoes", 5))
    modelo = args.modelo or m.get("modelo")
    temperatura = m.get("temperatura", 0.7)
    max_tokens = int(m.get("max_tokens", 4000))
    timeout = int(m.get("timeout", 900))
    juiz = m.get("juiz", {})
    # Ex.: ["--no-think"]. Muda o regime do modelo (com ou sem raciocínio), então é parte do
    # que foi medido e vai para o resumo.
    extras = list(m.get("argumentos_backend", []))
    semente = int(m.get("semente", 0)) if args.semente is None else args.semente

    avisos = []
    if "controle" in bracos and "tratamento" in bracos and bracos["controle"] and bracos["tratamento"]:
        a, b = len(bracos["controle"].encode()), len(bracos["tratamento"].encode())
        if abs(a - b) / max(a, b) > TOLERANCIA_DE_TAMANHO:
            avisos.append(f"controle ({a} B) e tratamento ({b} B) diferem mais de "
                          f"{int(TOLERANCIA_DE_TAMANHO*100)}%: o efeito pode ser de tamanho, não de conteúdo")
    if "controle" not in bracos:
        avisos.append("sem braço 'controle': uma diferença contra a base não separa conteúdo de "
                      "'qualquer instrução a mais'")
    if any(c.get("rubrica") for c in casos) and not juiz.get("modelo"):
        avisos.append("juiz sem modelo declarado: usa o mesmo padrão do backend — de preferência, "
                      "outra família (skill critico-independente)")

    tarefas = [(b, c["id"], r) for b in bracos for c in casos for r in range(reps)]
    # Ordem embaralhada: deriva do gateway ao longo do tempo (carga, cache, troca de réplica)
    # não pode cair inteira sobre um braço só.
    random.Random(semente).shuffle(tarefas)
    por_id = {c["id"]: c for c in casos}

    estampa = time.strftime("%Y%m%d-%H%M%S")
    saida_dir = Path(args.saida) if args.saida else manifesto_path.parent / "execucoes" / estampa
    saida_dir.mkdir(parents=True, exist_ok=True)
    registro = (saida_dir / "chamadas.jsonl").open("w", encoding="utf-8")

    def uma(t):
        braco, cid, rep = t
        caso = por_id[cid]
        resposta, erro, dt = chamar(backend, bracos[braco], caso["pedido_texto"], modelo,
                                    temperatura, max_tokens, timeout, extras)
        veredito, motivo = None, erro
        if resposta is not None:
            veredito, motivo = corrigir_regex(caso, resposta)
            if veredito and caso.get("rubrica"):
                veredito, motivo = corrigir_juiz(caso, resposta, backend, juiz, timeout)
        return dict(braco=braco, caso=cid, rep=rep, veredito=veredito, motivo=motivo,
                    segundos=dt, resposta=resposta)

    resultados = []
    with cf.ThreadPoolExecutor(max_workers=max(1, args.paralelo)) as ex:
        for i, res in enumerate(ex.map(uma, tarefas), 1):
            resultados.append(res)
            registro.write(json.dumps(res, ensure_ascii=False) + "\n")
            if not args.silencioso:
                print(f"\r  {i}/{len(tarefas)} chamadas", end="", file=sys.stderr, flush=True)
    registro.close()
    if not args.silencioso:
        print(file=sys.stderr)

    # Agregação: por braço no total, e por braço × caso.
    def contar(filtro):
        sel = [r for r in resultados if filtro(r)]
        ok = sum(1 for r in sel if r["veredito"] is True)
        nok = sum(1 for r in sel if r["veredito"] is False)
        err = sum(1 for r in sel if r["veredito"] is None)
        return ok, nok, err

    registrado = pre_registro(manifesto_path)
    sobrepostos = [n for n in ("modelo", "repeticoes", "casos", "semente") if getattr(args, n) is not None]
    if sobrepostos and registrado.startswith("sim"):
        # O commit registrou um experimento; a linha de comando rodou outro.
        registrado = f"não — {', '.join(sobrepostos)} sobreposto(s) na linha de comando: exploratório"
    resumo = {"id": m["id"], "manifesto_sha256": hashlib.sha256(manifesto_path.read_bytes()).hexdigest()[:16],
              "pre_registrado": registrado, "modelo": modelo or "(padrão do backend)",
              "juiz": juiz.get("modelo") or "(padrão do backend)", "repeticoes": reps, "semente": semente,
              "argumentos_backend": extras,
              "casos": [c["id"] for c in casos], "bracos": {}, "por_caso": {}, "avisos": avisos}
    for b in bracos:
        ok, nok, err = contar(lambda r: r["braco"] == b)
        lo, hi = wilson(ok, ok + nok)
        resumo["bracos"][b] = dict(acertos=ok, falhas=nok, erros=err, ic95=[round(lo, 3), round(hi, 3)])
        for c in casos:
            ok2, nok2, err2 = contar(lambda r: r["braco"] == b and r["caso"] == c["id"])
            resumo["por_caso"].setdefault(c["id"], {})[b] = f"{ok2}/{ok2 + nok2}" + (f" (+{err2} erro)" if err2 else "")

    # Por tipo de caso: o critério de refutação típico separa "falha" de "não-regressão", e a soma
    # dos dois esconde exatamente o que se quer ver — conserta um, estraga o outro, média igual.
    tipo_de = {c["id"]: c.get("tipo") for c in casos}
    resumo["por_tipo"] = {}
    for tipo in sorted({t for t in tipo_de.values() if t}):
        for b in bracos:
            ok, nok, err = contar(lambda r: r["braco"] == b and tipo_de[r["caso"]] == tipo)
            lo, hi = wilson(ok, ok + nok)
            resumo["por_tipo"].setdefault(tipo, {})[b] = dict(acertos=ok, falhas=nok, erros=err,
                                                              ic95=[round(lo, 3), round(hi, 3)])

    def comparar(grupo):
        if "controle" not in grupo or "tratamento" not in grupo:
            return None
        c, t = grupo["controle"]["ic95"], grupo["tratamento"]["ic95"]
        if t[0] > c[1]:
            return "tratamento ACIMA — intervalos separados"
        if t[1] < c[0]:
            return "tratamento ABAIXO — intervalos separados"
        return "intervalos se sobrepõem — diferença NÃO demonstrada"

    total_err = sum(v["erros"] for v in resumo["bracos"].values())
    invalido = total_err / len(resultados) > TETO_DE_ERROS
    resumo["valido"] = not invalido
    if comparar(resumo["bracos"]):
        resumo["tratamento_vs_controle"] = comparar(resumo["bracos"])
    for tipo, grupo in resumo["por_tipo"].items():
        if comparar(grupo):
            grupo["tratamento_vs_controle"] = comparar(grupo)
    (saida_dir / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    imprimir(resumo, saida_dir)
    return 1 if invalido else 0


def imprimir(r, saida_dir):
    print(f"\n{r['id']} — modelo {r['modelo']}, juiz {r['juiz']}, {r['repeticoes']} repetição(ões), "
          f"semente {r['semente']}" + (f", backend {' '.join(r['argumentos_backend'])}"
                                       if r.get("argumentos_backend") else ""))
    print(f"pré-registrado: {r['pre_registrado']} · manifesto sha256:{r['manifesto_sha256']}\n")
    print(f"  {'braço':<12} {'acertos':>8} {'falhas':>7} {'erros':>6}   IC95 (Wilson)")
    for b, v in r["bracos"].items():
        n = v["acertos"] + v["falhas"]
        taxa = f"{v['acertos']}/{n}" if n else "—"
        print(f"  {b:<12} {taxa:>8} {v['falhas']:>7} {v['erros']:>6}   "
              f"[{v['ic95'][0]:.2f}, {v['ic95'][1]:.2f}]")
    print("\n  por caso:")
    for cid, por_braco in r["por_caso"].items():
        print(f"    {cid:<24} " + "  ".join(f"{b}={s}" for b, s in por_braco.items()))
    if "tratamento_vs_controle" in r:
        print(f"\n  tratamento × controle, todos os casos: {r['tratamento_vs_controle']}")
    for tipo, grupo in r.get("por_tipo", {}).items():
        linhas = "  ".join(f"{b}={v['acertos']}/{v['acertos'] + v['falhas']} "
                           f"[{v['ic95'][0]:.2f}, {v['ic95'][1]:.2f}]"
                           for b, v in grupo.items() if isinstance(v, dict))
        print(f"  tipo {tipo}: {linhas}")
        if "tratamento_vs_controle" in grupo:
            print(f"    tratamento × controle: {grupo['tratamento_vs_controle']}")
    for a in r["avisos"]:
        print(f"  aviso: {a}")
    if not r["valido"]:
        print(f"\n  RESULTADO INVÁLIDO: mais de {int(TETO_DE_ERROS*100)}% das chamadas deram erro de backend.")
    # O que este executor não mede, impresso sempre — "rodou" não é "está provado".
    print("\n  não medido aqui: uso de ferramentas e várias voltas (só turno único); outros modelos "
          "além do declarado; casos fora do manifesto.")
    print(f"  registro: {saida_dir}/chamadas.jsonl · resumo: {saida_dir}/resumo.json")


# --------------------------------------------------------------------------------------------
# Autoteste: backend falso e determinístico. Nenhuma rede, nenhuma credencial.

BACKEND_FALSO = r'''#!/usr/bin/env python3
import sys
a = sys.argv[1:]
sistema = a[a.index("-s") + 1] if "-s" in a else ""
pedido = open(a[a.index("-f") + 1], encoding="utf-8").read()
if "ERRO-DE-REDE" in pedido and "RUBRICA" not in sistema:
    sys.stderr.write("falha simulada\n"); sys.exit(1)
if sistema.startswith("RUBRICA"):
    resposta = pedido.split("## Resposta do modelo avaliado", 1)[1]
    print("PASSA\nmediu antes de afirmar" if "medi" in resposta else "FALHA\nafirmou sem medir")
elif "TRATAMENTO" in sistema:
    print("Antes de afirmar, medi: rodei a checagem e obtive o resultado.")
else:
    print("As branches divergem.")
'''


def autoteste():
    falhas = []
    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        backend = d / "backend-falso"
        backend.write_text(BACKEND_FALSO, encoding="utf-8")
        backend.chmod(0o755)
        (d / "controle.md").write_text("Seja cuidadoso e responda com clareza, conferindo o raciocínio.\n" * 3)
        (d / "tratamento.md").write_text("TRATAMENTO: meça antes de afirmar, diga o que mediu.\n")
        (d / "rubrica.md").write_text("RUBRICA: PASSA se mediu antes de afirmar.\n")
        (d / "p1.md").write_text("As branches divergem?\n")
        (d / "p2.md").write_text("Isto é ERRO-DE-REDE?\n")
        manifesto = {
            "id": "EXP-AUTOTESTE", "hipotese": "h", "criterio_de_refutacao": "c",
            "repeticoes": 6, "semente": 7,
            "bracos": {"base": None, "controle": "controle.md", "tratamento": "tratamento.md"},
            "casos": [
                {"id": "juiz", "tipo": "falha", "pedido": "p1.md", "rubrica": "rubrica.md"},
                {"id": "regex", "tipo": "nao-regressao", "pedido": "p1.md", "deve_conter": ["medi"],
                 "nao_deve_conter": ["divergem"]},
            ],
        }
        mp = d / "experimento.json"
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        args = argparse.Namespace(backend=str(backend), repeticoes=None, modelo="falso", casos=None,
                                  saida=str(d / "out"), paralelo=4, semente=None, silencioso=True)
        import io, contextlib
        with contextlib.redirect_stdout(io.StringIO()):
            codigo = executar(mp, args)
        r = json.loads((d / "out" / "resumo.json").read_text(encoding="utf-8"))
        esperado = {"base": (0, 12), "controle": (0, 12), "tratamento": (12, 0)}
        for b, (ok, nok) in esperado.items():
            got = (r["bracos"][b]["acertos"], r["bracos"][b]["falhas"])
            if got != (ok, nok):
                falhas.append(f"braço {b}: esperava acertos/falhas {(ok, nok)}, obtive {got}")
        if codigo != 0:
            falhas.append(f"execução válida saiu {codigo}")
        pt = r.get("por_tipo", {})
        got = {t: (pt.get(t, {}).get("tratamento", {}).get("acertos"), pt.get(t, {}).get("base", {}).get("falhas"))
               for t in ("falha", "nao-regressao")}
        if got != {"falha": (6, 6), "nao-regressao": (6, 6)} or "ACIMA" not in pt.get("falha", {}).get("tratamento_vs_controle", ""):
            falhas.append(f"agregação por tipo errada: {got}")
        if r.get("tratamento_vs_controle", "").split()[1:2] != ["ACIMA"]:
            falhas.append(f"tratamento claramente melhor não foi declarado separado: {r.get('tratamento_vs_controle')}")
        if not r["pre_registrado"].startswith("não"):
            falhas.append(f"manifesto fora do git foi dado como pré-registrado: {r['pre_registrado']}")
        if not any("diferem mais de" in a for a in r["avisos"]):
            falhas.append("controle e tratamento de tamanhos muito diferentes não geraram aviso")
        linhas = (d / "out" / "chamadas.jsonl").read_text(encoding="utf-8").splitlines()
        if len(linhas) != 36:
            falhas.append(f"registro com {len(linhas)} chamadas, esperava 36")

        # Erro de backend: não pode virar falha do braço, e acima do teto invalida o resultado.
        manifesto["casos"] = [{"id": "rede", "pedido": "p2.md", "deve_conter": ["x"]}]
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        args.saida = str(d / "out2")
        with contextlib.redirect_stdout(io.StringIO()):
            codigo = executar(mp, args)
        r = json.loads((d / "out2" / "resumo.json").read_text(encoding="utf-8"))
        if any(v["falhas"] for v in r["bracos"].values()):
            falhas.append("erro de backend contado como falha do braço")
        if codigo != 1 or r["valido"]:
            falhas.append(f"100% de erro de backend não invalidou o resultado (saída {codigo})")

        # Manifesto sem critério de refutação é recusado antes de qualquer chamada.
        del manifesto["criterio_de_refutacao"]
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        p = subprocess.run([sys.executable, "-I", __file__, str(mp), "--backend", str(backend)],
                           capture_output=True, text=True)
        if p.returncode != 2 or "criterio_de_refutacao" not in p.stderr:
            falhas.append(f"manifesto sem critério de refutação não foi recusado (saída {p.returncode})")

    # Wilson: valores conhecidos.
    lo, hi = wilson(0, 10)
    if not (lo == 0.0 and 0.27 < hi < 0.28):
        falhas.append(f"wilson(0,10) = ({lo:.3f}, {hi:.3f}), esperava (0, ~0.278)")

    if falhas:
        for f in falhas:
            print(f"  \033[31mFALHOU:\033[0m {f}", file=sys.stderr)
        print(f"\033[31mautoteste: {len(falhas)} checagem(ns) falharam\033[0m", file=sys.stderr)
        return 3
    print("\033[32mautoteste: 10 checagens corretas — contagem por braço e por tipo, separação, pré-registro, "
          "aviso de tamanho, registro, erro ≠ falha, invalidação, critério obrigatório, Wilson\033[0m")
    return 0


def main():
    ap = argparse.ArgumentParser(description="Experimento controlado de instrução, com controle e repetição.")
    ap.add_argument("manifesto", nargs="?", help="experimento.json")
    ap.add_argument("--autoteste", action="store_true")
    ap.add_argument("--backend", help=f"executável com interface do oa-chat (padrão: {BACKEND_PADRAO})")
    ap.add_argument("--modelo", help="sobrepõe o modelo do manifesto (torna a execução exploratória)")
    ap.add_argument("--repeticoes", type=int, help="sobrepõe as repetições (para ensaio de fumaça)")
    ap.add_argument("--casos", nargs="+", help="só estes casos")
    ap.add_argument("--semente", type=int)
    ap.add_argument("--paralelo", type=int, default=4, help="chamadas simultâneas (padrão 4)")
    ap.add_argument("--saida", help="diretório do registro (padrão: <experimento>/execucoes/<data>)")
    ap.add_argument("--silencioso", action="store_true")
    args = ap.parse_args()
    if args.autoteste:
        sys.exit(autoteste())
    if not args.manifesto:
        ap.error("informe o manifesto ou --autoteste")
    sys.exit(executar(Path(args.manifesto).resolve(), args))


if __name__ == "__main__":
    main()
