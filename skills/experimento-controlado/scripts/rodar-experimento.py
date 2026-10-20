#!/usr/bin/env python3
# Caminho relativo: skills/experimento-controlado/scripts/rodar-experimento.py
#
# Roda um experimento controlado de instrução (prompt, regra, skill): cada caso, em cada braço,
# repetido N vezes, em ordem embaralhada, corrigido sem que o corretor saiba o braço. Imprime a
# taxa de acerto por braço com intervalo de Wilson a 95% e compara o tratamento com cada outro
# braço pela diferença estratificada por caso (Mantel-Haenszel), com o intervalo dela.
#
#   rodar-experimento.py docs/experimentos/EXP-0001-x/experimento.json
#   rodar-experimento.py <manifesto> --repeticoes 1 --casos divergencia   # ensaio de fumaça
#   rodar-experimento.py <manifesto> --amostra-gabarito <chamadas.jsonl> 30 > gabarito.jsonl
#   rodar-experimento.py <manifesto> --calibrar-juiz gabarito.jsonl       # juiz × correção humana
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
# Resposta do juiz fora do formato também não é falha, e também não é erro de backend: vai para
# a coluna dela. No EXP-0001 o juiz escreveu `FALHA: motivo` numa linha só, e as três falhas
# sumiram da conta como "erro".
#
# Pré-registro: vale para TODAS as entradas — manifesto, braços, casos e rubricas. Rubrica
# editada depois do resultado é critério editado depois do resultado.
#
# Códigos: 0 rodou · 1 resultado inválido (erros demais) ou juiz abaixo da concordância mínima
#          · 2 uso/manifesto · 3 autoteste falhou
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
# Juiz que discorda da correção humana em mais de 15% dos casos mede o juiz, não o braço.
CONCORDANCIA_MINIMA = 0.85
# Primeira linha do juiz: `PASSA`, `FALHA`, `**FALHA**`, `FALHA: motivo` e `Falha — motivo` valem.
VEREDITO = re.compile(r"^\W*(PASSA|FALHA)\b\W*(.*)$", re.I)


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


def diferenca_estratificada(estratos, z=1.96):
    """Diferença de taxa tratamento − outro, estratificada por caso (Mantel-Haenszel), com a
    variância de Sato. estratos: [(acertos_t, n_t, acertos_o, n_o)], um por caso.

    Por que estratificar: as repetições de um caso são correlacionadas entre si, e somá-las como
    se fossem amostras independentes conta 30 onde há 3. Dentro do caso elas são independentes
    (sorteio a temperatura > 0), e é isso que a estratificação usa. Generalizar para casos FORA do
    manifesto é outra pergunta — ver `casos_favoraveis`.
    """
    estratos = [e for e in estratos if e[1] and e[3]]
    W = sum(nt * no / (nt + no) for _, nt, _, no in estratos)
    if not W:
        return None
    rd = sum((at * no - ao * nt) / (nt + no) for at, nt, ao, no in estratos) / W
    P = sum((nt * nt * ao - no * no * at + nt * no * (no - nt) / 2) / (nt + no) ** 2
            for at, nt, ao, no in estratos)
    Q = sum((at * (no - ao) + ao * (nt - at)) / (2 * (nt + no)) for at, nt, ao, no in estratos)
    meia = z * math.sqrt(max(rd * P + Q, 0.0)) / W
    return rd, rd - meia, rd + meia


def leitura(dif):
    if dif is None:
        return "sem dados"
    if dif[1] > 0:
        return "tratamento ACIMA"
    if dif[2] < 0:
        return "tratamento ABAIXO"
    return "inconclusivo — o intervalo da diferença contém zero"


def entradas(m, base, manifesto_path):
    """Todo arquivo que decide o resultado: o manifesto e o que ele referencia."""
    arqs = [manifesto_path]
    arqs += [base / a for a in m["bracos"].values() if a]
    for c in m["casos"]:
        arqs += [base / c[k] for k in ("pedido", "rubrica") if c.get(k)]
    return sorted({p.resolve() for p in arqs})


def sha_das_entradas(arqs, base):
    h = hashlib.sha256()
    raiz = base.resolve()
    for p in arqs:
        nome = p.relative_to(raiz).as_posix() if p.is_relative_to(raiz) else str(p)
        h.update(nome.encode() + b"\0" + p.read_bytes() + b"\0")
    return h.hexdigest()[:16]


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
    ids = {c["id"] for c in m["casos"]}
    for c in m["casos"]:
        # Gêmeo: mesmo assunto, mas a evidência DECIDE — afirmar direto é o certo. Sem ele, quem
        # ressalva tudo passa em todos os casos de falha e parece calibrado.
        if c.get("gemeo_de") and c["gemeo_de"] not in ids:
            falhar(f"caso '{c['id']}': gemeo_de aponta para caso inexistente: {c['gemeo_de']}")
    return m, bracos, casos


def pre_registro(arqs):
    """'sim (<commit>)' se TODAS as entradas estão versionadas e sem alteração; senão, exploratório.

    Só lê o git. Critério alterado depois de ver resultado é o que transforma experimento em
    narrativa — o commit é a data que prova que o critério veio antes. E o critério não mora só
    no manifesto: rubrica, caso e braço editados depois do resultado mudam o que foi medido.
    Até 2026-10-16 esta função olhava só o `experimento.json`.
    """
    d = str(arqs[0].parent)
    nomes = [str(a) for a in arqs]
    try:
        sujo = subprocess.run(["git", "-C", d, "status", "--porcelain", "--untracked-files=all", "--", *nomes],
                              capture_output=True, text=True, timeout=30)
        if sujo.returncode != 0:
            return "não — fora de repositório git: exploratório"
        if sujo.stdout.strip():
            alterados = ", ".join(l[3:].rsplit("/", 1)[-1] for l in sujo.stdout.splitlines()[:3])
            return f"não — entrada alterada ou não versionada ({alterados}): exploratório"
        c = subprocess.run(["git", "-C", d, "log", "-1", "--format=%h %cs", "--", *nomes],
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
    """O juiz vê o pedido e a resposta, nunca o braço. Primeira linha: PASSA ou FALHA.

    Devolve (veredito, motivo, tipo_de_erro); tipo_de_erro é None, "juiz" (o backend do juiz
    falhou) ou "juiz-formato" (respondeu, mas sem veredito legível).
    """
    pedido = (f"## Pedido feito ao modelo avaliado\n\n{caso['pedido_texto']}\n\n"
              f"## Resposta do modelo avaliado\n\n{resposta}\n\n"
              "Responda na PRIMEIRA linha apenas PASSA ou FALHA. Na segunda, o motivo em uma frase.")
    saida, erro, _ = chamar(backend, caso["rubrica_texto"], pedido, juiz.get("modelo"),
                            juiz.get("temperatura", 0), juiz.get("max_tokens", 2000), timeout,
                            juiz.get("argumentos_backend", []))
    if erro:
        return None, f"juiz: {erro}", "juiz"
    linhas = [l.strip() for l in saida.strip().splitlines() if l.strip()]
    m = VEREDITO.match(linhas[0]) if linhas else None
    if not m:
        return None, f"juiz fora do formato: {saida.strip()[:120]!r}", "juiz-formato"
    motivo = m.group(2).strip() or (linhas[1] if len(linhas) > 1 else "")
    return m.group(1).upper() == "PASSA", f"juiz: {motivo}", None


def executar(manifesto_path, args):
    m, bracos, casos = carregar(manifesto_path, args.casos)
    # As entradas do manifesto INTEIRO, mesmo com --casos: o pré-registro é do experimento.
    arqs = entradas(m, manifesto_path.parent, manifesto_path)
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
    # Todo braço com prompt se mede contra o tratamento em tamanho. O braço que é curto de
    # propósito (ex.: "mínimo", uma frase) se declara em `bracos_de_tamanho_livre`.
    livres = set(m.get("bracos_de_tamanho_livre", []))
    if bracos.get("tratamento"):
        t = len(bracos["tratamento"].encode())
        for nome, texto in bracos.items():
            if nome == "tratamento" or not texto or nome in livres:
                continue
            a = len(texto.encode())
            if abs(a - t) / max(a, t) > TOLERANCIA_DE_TAMANHO:
                avisos.append(f"{nome} ({a} B) e tratamento ({t} B) diferem mais de "
                              f"{int(TOLERANCIA_DE_TAMANHO*100)}%: o efeito pode ser de tamanho, não de conteúdo")
    if "controle" not in bracos:
        avisos.append("sem braço 'controle': uma diferença contra a base não separa conteúdo de "
                      "'qualquer instrução a mais'")
    if any(c.get("rubrica") for c in casos) and not juiz.get("modelo"):
        avisos.append("juiz sem modelo declarado: usa o mesmo padrão do backend — de preferência, "
                      "outra família (skill critico-independente)")
    if any(c.get("tipo") == "falha" for c in casos) and not any(c.get("gemeo_de") for c in casos):
        avisos.append("caso de falha sem gêmeo: um braço que ressalva tudo passa em todos e parece "
                      "calibrado — dê a cada caso de falha um gêmeo em que a evidência decide")

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
        veredito, motivo, tipo_erro = None, erro, ("backend" if erro else None)
        if resposta is not None:
            veredito, motivo = corrigir_regex(caso, resposta)
            if veredito and caso.get("rubrica"):
                veredito, motivo, tipo_erro = corrigir_juiz(caso, resposta, backend, juiz, timeout)
        return dict(braco=braco, caso=cid, rep=rep, veredito=veredito, motivo=motivo,
                    erro=tipo_erro, segundos=dt, resposta=resposta)

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

    registrado = pre_registro(arqs)
    sobrepostos = [n for n in ("modelo", "repeticoes", "casos", "semente") if getattr(args, n) is not None]
    if sobrepostos and registrado.startswith("sim"):
        # O commit registrou um experimento; a linha de comando rodou outro.
        registrado = f"não — {', '.join(sobrepostos)} sobreposto(s) na linha de comando: exploratório"
    resumo = {"id": m["id"], "manifesto_sha256": hashlib.sha256(manifesto_path.read_bytes()).hexdigest()[:16],
              "entradas_sha256": sha_das_entradas(arqs, manifesto_path.parent),
              "executor_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16],
              "pre_registrado": registrado, "modelo": modelo or "(padrão do backend)",
              "juiz": juiz.get("modelo") or "(padrão do backend)", "repeticoes": reps, "semente": semente,
              "argumentos_backend": extras, "casos": [c["id"] for c in casos], "avisos": avisos}
    resumo.update(agregar(resultados, bracos, casos))
    invalido = resumo["erros_total"] / len(resultados) > TETO_DE_ERROS
    resumo["valido"] = not invalido
    (saida_dir / "resumo.json").write_text(json.dumps(resumo, ensure_ascii=False, indent=2), encoding="utf-8")

    imprimir(resumo, saida_dir)
    return 1 if invalido else 0


def agregar(resultados, bracos, casos):
    """Contagens por braço, por caso, por tipo e por par; diferenças do tratamento contra cada
    outro braço. Separada de `executar` para que o autoteste e a releitura de um registro antigo
    (`--reagregar`) usem a mesma conta."""
    def contar(sel):
        ok = sum(1 for r in sel if r["veredito"] is True)
        nok = sum(1 for r in sel if r["veredito"] is False)
        erros = {}
        for r in sel:
            if r["veredito"] is None:
                k = r.get("erro") or "backend"
                erros[k] = erros.get(k, 0) + 1
        lo, hi = wilson(ok, ok + nok)
        return dict(acertos=ok, falhas=nok, erros=sum(erros.values()), erros_por_tipo=erros,
                    ic95=[round(lo, 3), round(hi, 3)])

    def de(b=None, c=None, tipo=None):
        return [r for r in resultados if (b is None or r["braco"] == b) and (c is None or r["caso"] == c)
                and (tipo is None or tipo_de.get(r["caso"]) == tipo)]

    tipo_de = {c["id"]: c.get("tipo") for c in casos}
    out = {"bracos": {}, "por_caso": {}, "por_tipo": {}, "pares": {}, "comparacoes": {}}
    for b in bracos:
        out["bracos"][b] = contar(de(b))
        tamanhos = sorted(len(r["resposta"]) for r in de(b) if r["resposta"] is not None)
        # Resposta mais longa tem mais chance de conter afirmação reprovável E ressalva aprovável:
        # o tamanho é confusão possível, e fica à vista.
        out["bracos"][b]["tamanho_mediano"] = tamanhos[len(tamanhos) // 2] if tamanhos else None
        for c in casos:
            v = contar(de(b, c["id"]))
            out["por_caso"].setdefault(c["id"], {})[b] = (f"{v['acertos']}/{v['acertos'] + v['falhas']}"
                                                          + (f" (+{v['erros']} erro)" if v["erros"] else ""))
    # Por tipo de caso: o critério de refutação típico separa "falha" de "não-regressão", e a soma
    # dos dois esconde exatamente o que se quer ver — conserta um, estraga o outro, média igual.
    tipos = sorted({t for t in tipo_de.values() if t})
    for tipo in tipos:
        for b in bracos:
            out["por_tipo"].setdefault(tipo, {})[b] = contar(de(b, tipo=tipo))

    # Par = caso de falha + gêmeo, na mesma repetição. Acerta o par quem ressalva onde a evidência
    # falta E afirma onde ela basta: é a calibração que a hipótese de ressalva quase sempre alega.
    pares = [(c["gemeo_de"], c["id"]) for c in casos if c.get("gemeo_de") and c["gemeo_de"] in tipo_de]
    for b in bracos:
        ok = n = 0
        for falha, gemeo in pares:
            v1 = {r["rep"]: r["veredito"] for r in de(b, falha)}
            v2 = {r["rep"]: r["veredito"] for r in de(b, gemeo)}
            for rep in v1.keys() & v2.keys():
                if v1[rep] is None or v2[rep] is None:
                    continue
                n += 1
                ok += v1[rep] and v2[rep]
        if pares:
            lo, hi = wilson(ok, n)
            out["pares"][b] = dict(acertos=ok, total=n, ic95=[round(lo, 3), round(hi, 3)])

    # Tratamento contra cada outro braço: diferença estratificada por caso, com intervalo; e em
    # quantos casos o tratamento ficou à frente — a única leitura que fala de casos FORA daqui.
    if "tratamento" in bracos:
        grupos = [("todos", [c["id"] for c in casos])] + [
            (tipo, [c["id"] for c in casos if c.get("tipo") == tipo]) for tipo in tipos]
        # Casos usados para ESCREVER o tratamento (`"origem": "desenho"`) se leem à parte dos
        # novos: o tratamento foi ajustado a eles, e o efeito ali é o teto, não a estimativa.
        origens = sorted({c["origem"] for c in casos if c.get("origem")})
        if len(origens) > 1:
            grupos += [(f"falha/{o}", [c["id"] for c in casos if c.get("origem") == o and c.get("tipo") == "falha"])
                       for o in origens]
        for outro in bracos:
            if outro == "tratamento":
                continue
            for nome, ids in grupos:
                estratos, favoraveis, contrarios = [], 0, 0
                for cid in ids:
                    t, o = contar(de("tratamento", cid)), contar(de(outro, cid))
                    nt, no = t["acertos"] + t["falhas"], o["acertos"] + o["falhas"]
                    estratos.append((t["acertos"], nt, o["acertos"], no))
                    if nt and no:
                        dt = t["acertos"] / nt - o["acertos"] / no
                        favoraveis += dt > 0
                        contrarios += dt < 0
                dif = diferenca_estratificada(estratos)
                out["comparacoes"].setdefault(outro, {})[nome] = dict(
                    diferenca=round(dif[0], 3) if dif else None,
                    ic95=[round(dif[1], 3), round(dif[2], 3)] if dif else None,
                    leitura=leitura(dif), casos_favoraveis=favoraveis, casos_contrarios=contrarios,
                    casos=len(ids))
            if pares:
                # Pares como estratos: cada par é um "caso" cujo acerto é acertar os dois.
                estratos = []
                for falha, gemeo in pares:
                    linha = []
                    for b in ("tratamento", outro):
                        v1 = {r["rep"]: r["veredito"] for r in de(b, falha)}
                        v2 = {r["rep"]: r["veredito"] for r in de(b, gemeo)}
                        ok = n = 0
                        for rep in v1.keys() & v2.keys():
                            if v1[rep] is not None and v2[rep] is not None:
                                n += 1
                                ok += v1[rep] and v2[rep]
                        linha += [ok, n]
                    estratos.append(tuple(linha))
                dif = diferenca_estratificada(estratos)
                out["comparacoes"][outro]["pares"] = dict(
                    diferenca=round(dif[0], 3) if dif else None,
                    ic95=[round(dif[1], 3), round(dif[2], 3)] if dif else None, leitura=leitura(dif),
                    casos_favoraveis=sum(1 for at, nt, ao, no in estratos if nt and no and at / nt > ao / no),
                    casos_contrarios=sum(1 for at, nt, ao, no in estratos if nt and no and at / nt < ao / no),
                    casos=len(estratos))
    out["erros_total"] = sum(v["erros"] for v in out["bracos"].values())
    return out


def imprimir(r, saida_dir):
    print(f"\n{r['id']} — modelo {r['modelo']}, juiz {r['juiz']}, {r['repeticoes']} repetição(ões), "
          f"semente {r['semente']}" + (f", backend {' '.join(r['argumentos_backend'])}"
                                       if r.get("argumentos_backend") else ""))
    print(f"pré-registrado: {r['pre_registrado']} · entradas sha256:{r.get('entradas_sha256', '?')} "
          f"· executor sha256:{r.get('executor_sha256', '?')}\n")
    print(f"  {'braço':<12} {'acertos':>8} {'falhas':>7} {'erros':>6}   {'IC95 (Wilson)':<14} tamanho mediano")
    for b, v in r["bracos"].items():
        n = v["acertos"] + v["falhas"]
        taxa = f"{v['acertos']}/{n}" if n else "—"
        tipos = ", ".join(f"{k} {q}" for k, q in v.get("erros_por_tipo", {}).items())
        print(f"  {b:<12} {taxa:>8} {v['falhas']:>7} {v['erros']:>6}   "
              f"[{v['ic95'][0]:.2f}, {v['ic95'][1]:.2f}]   {v.get('tamanho_mediano') or '—'} car."
              + (f"   ({tipos})" if tipos else ""))
    print("\n  por caso:")
    for cid, por_braco in r["por_caso"].items():
        print(f"    {cid:<28} " + "  ".join(f"{b}={s}" for b, s in por_braco.items()))
    for tipo, grupo in r.get("por_tipo", {}).items():
        linhas = "  ".join(f"{b}={v['acertos']}/{v['acertos'] + v['falhas']}" for b, v in grupo.items())
        print(f"  tipo {tipo}: {linhas}")
    if r.get("pares"):
        print("  pares (falha + gêmeo, mesma repetição): " + "  ".join(
            f"{b}={v['acertos']}/{v['total']}" for b, v in r["pares"].items()))
    if r.get("comparacoes"):
        print("\n  tratamento − outro braço, estratificado por caso (IC95):")
        for outro, grupos in r["comparacoes"].items():
            for nome, v in grupos.items():
                if v["diferenca"] is None:
                    continue
                print(f"    × {outro:<10} {nome:<14} {v['diferenca']:+.2f} [{v['ic95'][0]:+.2f}, {v['ic95'][1]:+.2f}]"
                      f"  {v['leitura']}  · à frente em {v['casos_favoraveis']} de {v['casos']} caso(s), "
                      f"atrás em {v['casos_contrarios']}")
    for a in r["avisos"]:
        print(f"  aviso: {a}")
    if not r["valido"]:
        print(f"\n  RESULTADO INVÁLIDO: mais de {int(TETO_DE_ERROS*100)}% das chamadas deram erro "
              f"(de backend ou de juiz).")
    # O que este executor não mede, impresso sempre — "rodou" não é "está provado".
    print("\n  não medido aqui: uso de ferramentas e várias voltas (só turno único); outros modelos "
          "além do declarado; casos fora do manifesto — o intervalo vale para ESTES casos, e a "
          "contagem de casos à frente é o único indício sobre os outros; a concordância do juiz, "
          "que se mede à parte com --calibrar-juiz.")
    print(f"  registro: {saida_dir}/chamadas.jsonl · resumo: {saida_dir}/resumo.json")


def ler_registro(caminho):
    try:
        return [json.loads(l) for l in Path(caminho).read_text(encoding="utf-8").splitlines() if l.strip()]
    except (OSError, json.JSONDecodeError) as e:
        falhar(f"registro ilegível: {caminho}: {e}")


def reagregar(manifesto_path, chamadas):
    """Relê um registro antigo com a conta de hoje. Sempre exploratório: o critério registrado
    daquele experimento é o que vale para ele; isto só mostra o que a conta nova diz.

    Recupera o veredito que o leitor antigo do juiz perdeu (`FALHA: motivo` numa linha só): o
    registro guardou os primeiros 120 caracteres da saída do juiz, e o veredito está neles.
    """
    m, bracos, casos = carregar(manifesto_path)
    resultados = ler_registro(chamadas)
    recuperados = 0
    for r in resultados:
        motivo = r.get("motivo") or ""
        if r["veredito"] is None and motivo.startswith("juiz fora do formato: "):
            bruto = motivo[len("juiz fora do formato: "):].strip("'\"")
            v = VEREDITO.match(bruto)
            if v:
                r["veredito"] = v.group(1).upper() == "PASSA"
                r["motivo"] = f"juiz (recuperado na releitura): {v.group(2)}"
                recuperados += 1
        elif r["veredito"] is None and not r.get("erro"):
            r["erro"] = "juiz-formato" if motivo.startswith("juiz fora") else (
                "juiz" if motivo.startswith("juiz") else "backend")
    reps = 1 + max((r["rep"] for r in resultados), default=0)
    resumo = {"id": m["id"], "pre_registrado": "não — RELEITURA de registro antigo: exploratório",
              "modelo": m.get("modelo"), "juiz": (m.get("juiz") or {}).get("modelo"), "repeticoes": reps,
              "semente": m.get("semente"), "argumentos_backend": m.get("argumentos_backend", []),
              "casos": [c["id"] for c in casos],
              "avisos": [f"{recuperados} veredito(s) do juiz recuperado(s) do formato que o leitor antigo perdia"]
              if recuperados else []}
    resumo.update(agregar(resultados, bracos, casos))
    resumo["valido"] = resumo["erros_total"] / max(1, len(resultados)) <= TETO_DE_ERROS
    imprimir(resumo, Path(chamadas).parent)
    return 0


def amostra_gabarito(manifesto_path, chamadas, n, semente):
    """Sorteia N respostas corrigidas por juiz, equilibradas entre casos, SEM braço e SEM o
    veredito do juiz — quem corrige à mão não pode saber nenhum dos dois. Escreve JSONL em
    stdout com `gabarito: null`, para a pessoa preencher com true/false (e `nota`, se quiser).
    """
    m, _, casos = carregar(manifesto_path)
    com_rubrica = {c["id"] for c in casos if c.get("rubrica")}
    pool = [r for r in ler_registro(chamadas) if r["caso"] in com_rubrica and r.get("resposta")]
    rnd = random.Random(semente)
    por_caso = {}
    for r in pool:
        por_caso.setdefault(r["caso"], []).append(r)
    for v in por_caso.values():
        rnd.shuffle(v)
    escolhidos, i = [], 0
    while len(escolhidos) < n and any(i < len(v) for v in por_caso.values()):
        for cid in sorted(por_caso):
            if i < len(por_caso[cid]) and len(escolhidos) < n:
                escolhidos.append(por_caso[cid][i])
        i += 1
    rnd.shuffle(escolhidos)
    for k, r in enumerate(escolhidos, 1):
        print(json.dumps({"id": f"G{k:03d}", "caso": r["caso"], "resposta": r["resposta"],
                          "gabarito": None, "nota": ""}, ensure_ascii=False))
    return 0


def calibrar_juiz(manifesto_path, gabarito, args):
    """Roda o juiz do manifesto sobre respostas já corrigidas à mão e mede a concordância.

    Juiz é instrumento; instrumento que não foi aferido não mede. Abaixo do mínimo
    (`juiz.concordancia_minima` no manifesto, padrão 0.85), sai com 1: o experimento não deve
    rodar com este juiz e esta rubrica. Resposta do juiz fora do formato conta como discordância.
    """
    m, _, casos = carregar(manifesto_path)
    por_id = {c["id"]: c for c in casos}
    juiz = m.get("juiz", {})
    minimo = float(juiz.get("concordancia_minima", CONCORDANCIA_MINIMA))
    backend = Path(args.backend or os.environ.get("EXPERIMENTO_BACKEND") or BACKEND_PADRAO)
    if not os.access(backend, os.X_OK):
        falhar(f"backend não executável: {backend}")
    itens = [g for g in ler_registro(gabarito) if g.get("gabarito") is not None]
    if not itens:
        falhar("gabarito sem nenhuma linha corrigida (campo `gabarito` true/false)")
    sem_rubrica = sorted({g["caso"] for g in itens if not por_id.get(g["caso"], {}).get("rubrica")})
    if sem_rubrica:
        falhar(f"caso(s) do gabarito sem rubrica neste manifesto: {', '.join(sem_rubrica)}")

    def um(g):
        v, motivo, _ = corrigir_juiz(por_id[g["caso"]], g["resposta"], backend, juiz,
                                     int(m.get("timeout", 900)))
        return g, v, motivo

    with cf.ThreadPoolExecutor(max_workers=max(1, args.paralelo)) as ex:
        res = list(ex.map(um, itens))
    concordam = sum(1 for g, v, _ in res if v is not None and v == bool(g["gabarito"]))
    n = len(res)
    # Kappa de Cohen: concordância descontado o acaso. Juiz que diz FALHA sempre concorda 80%
    # com um gabarito 80% FALHA, e tem kappa zero.
    validos = [(bool(g["gabarito"]), v) for g, v, _ in res if v is not None]
    po = concordam / n
    if validos:
        ph = sum(h for h, _ in validos) / len(validos)
        pj = sum(j for _, j in validos) / len(validos)
        pe = ph * pj + (1 - ph) * (1 - pj)
        kappa = (po - pe) / (1 - pe) if pe < 1 else float("nan")
    else:
        kappa = float("nan")
    lo, hi = wilson(concordam, n)
    print(f"\njuiz {juiz.get('modelo') or '(padrão do backend)'} × gabarito humano — {n} resposta(s)")
    print(f"  concordância {concordam}/{n} = {po:.2f}  IC95 [{lo:.2f}, {hi:.2f}]  · kappa {kappa:.2f}"
          f"  · mínimo exigido {minimo:.2f}")
    for cid in sorted({g["caso"] for g, _, _ in res}):
        sel = [(g, v) for g, v, _ in res if g["caso"] == cid]
        c = sum(1 for g, v in sel if v is not None and v == bool(g["gabarito"]))
        print(f"    {cid:<28} {c}/{len(sel)}")
    disc = [(g, v, mo) for g, v, mo in res if v is None or v != bool(g["gabarito"])]
    if disc:
        print("\n  discordâncias:")
        for g, v, mo in disc:
            humano = "PASSA" if g["gabarito"] else "FALHA"
            juizv = {True: "PASSA", False: "FALHA", None: "ilegível"}[v]
            print(f"    {g.get('id', '?')} {g['caso']}: humano {humano}, juiz {juizv} — {mo[:160]}")
    aprovado = lo >= minimo if args.exigir_limite_inferior else po >= minimo
    print(f"\n  {'APROVADO' if aprovado else 'REPROVADO'}: "
          + ("o juiz pode corrigir este experimento." if aprovado else
             "o juiz mede a si mesmo, não o braço. Troque rubrica, modelo do juiz ou formato antes de rodar."))
    return 0 if aprovado else 1


# --------------------------------------------------------------------------------------------
# Autoteste: backend falso e determinístico. Nenhuma rede, nenhuma credencial.
#
# O "modelo" falso tem dois comportamentos: o tratamento RESSALVA SEMPRE ("medi antes de
# afirmar"), os outros braços AFIRMAM SEMPRE ("as branches divergem"). É o caso que o EXP-0001
# não conseguia distinguir: quem ressalva tudo ganha no caso de falha e perde no gêmeo.

BACKEND_FALSO = r'''#!/usr/bin/env python3
import sys
a = sys.argv[1:]
sistema = a[a.index("-s") + 1] if "-s" in a else ""
pedido = open(a[a.index("-f") + 1], encoding="utf-8").read()
if "ERRO-DE-REDE" in pedido and "RUBRICA" not in sistema:
    sys.stderr.write("falha simulada\n"); sys.exit(1)
if sistema.startswith("RUBRICA-INDECISA"):
    print("talvez")
elif sistema.startswith("RUBRICA"):
    resposta = pedido.split("## Resposta do modelo avaliado", 1)[1]
    # FALHA numa linha só, com o motivo junto: o formato que o leitor antigo perdia.
    print("PASSA\nmediu antes de afirmar" if "medi" in resposta else "FALHA: afirmou sem medir")
elif "TRATAMENTO" in sistema:
    print("Antes de afirmar, medi: rodei a checagem e obtive o resultado.")
else:
    print("As branches divergem.")
'''


def autoteste():
    import contextlib
    import io
    import shutil
    falhas = []
    checagens = []

    def checar(nome, ok, detalhe):
        checagens.append(nome)
        if not ok:
            falhas.append(f"{nome}: {detalhe}")

    def rodar(mp, saida, **kw):
        a = argparse.Namespace(backend=str(backend), repeticoes=None, modelo=None, casos=None,
                               saida=str(saida), paralelo=4, semente=None, silencioso=True)
        for k, v in kw.items():
            setattr(a, k, v)
        with contextlib.redirect_stdout(io.StringIO()):
            codigo = executar(mp, a)
        return codigo, json.loads((Path(saida) / "resumo.json").read_text(encoding="utf-8"))

    with tempfile.TemporaryDirectory() as d:
        d = Path(d)
        backend = d / "backend-falso"
        backend.write_text(BACKEND_FALSO, encoding="utf-8")
        backend.chmod(0o755)
        exp = d / "exp"
        exp.mkdir()
        (exp / "controle.md").write_text("Seja cuidadoso e responda com clareza, conferindo o raciocínio.\n" * 3)
        (exp / "tratamento.md").write_text("TRATAMENTO: meça antes de afirmar, diga o que mediu.\n")
        (exp / "rubrica.md").write_text("RUBRICA: PASSA se mediu antes de afirmar.\n")
        (exp / "rubrica-indecisa.md").write_text("RUBRICA-INDECISA: o juiz não decide.\n")
        (exp / "p1.md").write_text("As branches divergem?\n")
        (exp / "p2.md").write_text("Isto é ERRO-DE-REDE?\n")
        (exp / "p3.md").write_text("O log mostra commits só em uma delas. As branches divergem?\n")
        manifesto = {
            "id": "EXP-AUTOTESTE", "hipotese": "h", "criterio_de_refutacao": "c",
            "modelo": "falso", "repeticoes": 6, "semente": 7,
            "bracos": {"base": None, "controle": "controle.md", "tratamento": "tratamento.md"},
            "casos": [
                {"id": "falha", "tipo": "falha", "pedido": "p1.md", "rubrica": "rubrica.md"},
                # Gêmeo: a evidência decide, e afirmar direto é o certo.
                {"id": "gemeo", "tipo": "gemeo", "gemeo_de": "falha", "pedido": "p3.md",
                 "deve_conter": ["divergem"], "nao_deve_conter": ["medi"]},
            ],
        }
        mp = exp / "experimento.json"
        mp.write_text(json.dumps(manifesto), encoding="utf-8")

        # 1. Contagem, juiz em uma linha só, pares, comparação estratificada.
        codigo, r = rodar(mp, d / "out1")
        got = {b: (v["acertos"], v["falhas"], v["erros"]) for b, v in r["bracos"].items()}
        checar("contagem por braço", got == {"base": (6, 6, 0), "controle": (6, 6, 0), "tratamento": (6, 6, 0)},
               f"obtive {got}")
        checar("`FALHA: motivo` em uma linha é falha, não erro",
               r["por_caso"]["falha"]["base"] == "0/6", f"obtive {r['por_caso']['falha']['base']}")
        pt = r["por_tipo"]
        checar("agregação por tipo", (pt["falha"]["tratamento"]["acertos"], pt["gemeo"]["tratamento"]["acertos"]) == (6, 0),
               f"obtive {pt}")
        checar("ressalva generalizada não acerta par",
               r["pares"]["tratamento"] == {"acertos": 0, "total": 6, "ic95": r["pares"]["tratamento"]["ic95"]},
               f"obtive {r['pares'].get('tratamento')}")
        cf_ = r["comparacoes"]["controle"]
        checar("diferença estratificada declara ACIMA no caso de falha", "ACIMA" in cf_["falha"]["leitura"],
               f"obtive {cf_['falha']}")
        checar("e ABAIXO no gêmeo", "ABAIXO" in cf_["gemeo"]["leitura"], f"obtive {cf_['gemeo']}")
        checar("execução válida sai 0", codigo == 0, f"saiu {codigo}")
        checar("aviso de tamanho", any("diferem mais de" in a for a in r["avisos"]), f"avisos {r['avisos']}")
        checar("tamanho mediano no resumo", all(v.get("tamanho_mediano") for v in r["bracos"].values()),
               f"obtive {[v.get('tamanho_mediano') for v in r['bracos'].values()]}")
        linhas = (d / "out1" / "chamadas.jsonl").read_text(encoding="utf-8").splitlines()
        checar("registro completo", len(linhas) == 36, f"{len(linhas)} chamadas, esperava 36")
        checar("fora do git não é pré-registrado", r["pre_registrado"].startswith("não"), r["pre_registrado"])

        # 2. Pré-registro cobre TODAS as entradas, não só o manifesto.
        if shutil.which("git"):
            g = ["git", "-C", str(exp), "-c", "user.name=autoteste", "-c", "user.email=autoteste@invalid",
                 "-c", "commit.gpgsign=false", "-c", "core.hooksPath=/dev/null"]
            subprocess.run(["git", "init", "-q", str(exp)], check=True)
            subprocess.run(g + ["add", "-A"], check=True)
            subprocess.run(g + ["commit", "-q", "-m", "pre-registro"], check=True)
            _, r = rodar(mp, d / "out-git1")
            checar("tudo commitado é pré-registrado", r["pre_registrado"].startswith("sim"), r["pre_registrado"])
            sha1 = r["entradas_sha256"]
            (exp / "rubrica.md").write_text("RUBRICA: PASSA se mediu antes de afirmar. Editada depois.\n")
            _, r = rodar(mp, d / "out-git2")
            checar("rubrica editada depois do commit derruba o pré-registro",
                   r["pre_registrado"].startswith("não") and "rubrica.md" in r["pre_registrado"], r["pre_registrado"])
            checar("e muda o hash das entradas", r["entradas_sha256"] != sha1, "hash igual")
            shutil.rmtree(exp / ".git")
        else:
            falhas.append("git ausente: o pré-registro não pôde ser testado")

        # 3. Erro de backend: não vira falha, e acima do teto invalida.
        manifesto["casos"] = [{"id": "rede", "pedido": "p2.md", "deve_conter": ["x"]}]
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        codigo, r = rodar(mp, d / "out2")
        checar("erro de backend não é falha", not any(v["falhas"] for v in r["bracos"].values()),
               f"obtive {r['bracos']}")
        checar("100% de erro invalida", codigo == 1 and not r["valido"], f"saiu {codigo}")

        # 4. Juiz fora do formato: coluna própria, nem falha nem erro de backend.
        manifesto["casos"] = [{"id": "indeciso", "pedido": "p1.md", "rubrica": "rubrica-indecisa.md"}]
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        _, r = rodar(mp, d / "out3")
        tipos = r["bracos"]["base"]["erros_por_tipo"]
        checar("juiz ilegível vai para coluna própria", tipos == {"juiz-formato": 6} and r["bracos"]["base"]["falhas"] == 0,
               f"obtive {tipos}")

        # 5. Calibração do juiz contra gabarito humano, e amostra cega para o gabarito.
        manifesto["casos"] = [{"id": "falha", "tipo": "falha", "pedido": "p1.md", "rubrica": "rubrica.md"}]
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        gab = d / "gabarito.jsonl"
        itens = [("medi e obtive", True), ("medi antes", True), ("as branches divergem", False),
                 ("as branches divergem, conferi no log", True)]  # humano PASSA, juiz FALHA
        gab.write_text("\n".join(json.dumps({"id": f"G{i}", "caso": "falha", "resposta": t, "gabarito": v})
                                 for i, (t, v) in enumerate(itens)), encoding="utf-8")
        a = argparse.Namespace(backend=str(backend), paralelo=2, exigir_limite_inferior=False)
        with contextlib.redirect_stdout(io.StringIO()):
            c_ruim = calibrar_juiz(mp, gab, a)
        gab.write_text("\n".join(json.dumps({"caso": "falha", "resposta": t, "gabarito": v})
                                 for t, v in itens[:3]), encoding="utf-8")
        with contextlib.redirect_stdout(io.StringIO()):
            c_bom = calibrar_juiz(mp, gab, a)
        checar("calibração reprova juiz abaixo do mínimo e aprova o que concorda", (c_ruim, c_bom) == (1, 0),
               f"saídas {(c_ruim, c_bom)}, esperava (1, 0)")
        buf = io.StringIO()
        with contextlib.redirect_stdout(buf):
            amostra_gabarito(mp, d / "out1" / "chamadas.jsonl", 5, 1)
        linhas = [json.loads(l) for l in buf.getvalue().splitlines()]
        checar("amostra do gabarito é cega a braço e veredito",
               len(linhas) == 5 and not any({"braco", "veredito", "motivo"} & l.keys() for l in linhas),
               f"chaves {sorted({k for l in linhas for k in l})}")

        # 6. Manifesto sem critério de refutação é recusado antes de qualquer chamada.
        del manifesto["criterio_de_refutacao"]
        mp.write_text(json.dumps(manifesto), encoding="utf-8")
        p = subprocess.run([sys.executable, "-I", __file__, str(mp), "--backend", str(backend)],
                           capture_output=True, text=True)
        checar("critério de refutação obrigatório", p.returncode == 2 and "criterio_de_refutacao" in p.stderr,
               f"saída {p.returncode}")

    # 7. Leitor do veredito do juiz.
    casos_v = {"PASSA": "PASSA", "**FALHA**": "FALHA", "FALHA: sem medir": "FALHA", "Falha — x": "FALHA",
               "passa.": "PASSA", "FALHAS graves": None, "talvez": None}
    got = {k: (VEREDITO.match(k).group(1).upper() if VEREDITO.match(k) else None) for k in casos_v}
    checar("leitor do veredito do juiz", got == casos_v, f"obtive {got}")

    # 8. Estatística: valores conhecidos.
    lo, hi = wilson(0, 10)
    checar("Wilson", lo == 0.0 and 0.27 < hi < 0.28, f"wilson(0,10) = ({lo:.3f}, {hi:.3f})")
    rd, lo, hi = diferenca_estratificada([(20, 30, 10, 30)])
    wald = 1.96 * math.sqrt((2 / 3 * 1 / 3) / 30 * 2)
    checar("diferença estratificada com um estrato = Wald", abs(rd - 1 / 3) < 1e-9 and abs((hi - rd) - wald) < 1e-9,
           f"obtive {rd:.4f} ± {hi - rd:.4f}, esperava 0.3333 ± {wald:.4f}")

    if falhas:
        for f in falhas:
            print(f"  \033[31mFALHOU:\033[0m {f}", file=sys.stderr)
        print(f"\033[31mautoteste: {len(falhas)} de {len(checagens)} checagem(ns) falharam\033[0m", file=sys.stderr)
        return 3
    print(f"\033[32mautoteste: {len(checagens)} checagens corretas\033[0m")
    for c in checagens:
        print(f"  ok  {c}")
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
    ap.add_argument("--reagregar", metavar="CHAMADAS",
                    help="relê um chamadas.jsonl antigo com a conta atual (exploratório, sem chamar modelo)")
    ap.add_argument("--amostra-gabarito", nargs=2, metavar=("CHAMADAS", "N"),
                    help="sorteia N respostas sem braço e sem veredito, para correção humana (JSONL em stdout)")
    ap.add_argument("--calibrar-juiz", metavar="GABARITO",
                    help="mede a concordância do juiz do manifesto com um gabarito corrigido à mão")
    ap.add_argument("--exigir-limite-inferior", action="store_true",
                    help="na calibração, exige que o limite inferior do IC95 passe do mínimo, não só a média")
    args = ap.parse_args()
    if args.autoteste:
        sys.exit(autoteste())
    if not args.manifesto:
        ap.error("informe o manifesto ou --autoteste")
    mp = Path(args.manifesto).resolve()
    if args.reagregar:
        sys.exit(reagregar(mp, args.reagregar))
    if args.amostra_gabarito:
        sys.exit(amostra_gabarito(mp, args.amostra_gabarito[0], int(args.amostra_gabarito[1]),
                                  args.semente if args.semente is not None else 1))
    if args.calibrar_juiz:
        sys.exit(calibrar_juiz(mp, args.calibrar_juiz, args))
    sys.exit(executar(mp, args))


if __name__ == "__main__":
    main()
