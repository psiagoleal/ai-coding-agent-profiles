#!/usr/bin/env python3
"""Temas da apresentação: lista, gera CSS, aplica no HTML, verifica contraste e deriva de uma marca.

Só biblioteca padrão. Fonte única dos temas: ../temas.json.

  tema.py listar
  tema.py css [--temas tecnico,auditorio]
  tema.py aplicar deck.html
  tema.py verificar [--tema nome] [--arquivo outro.json]
  tema.py derivar --nome marca --primaria "#c8102e" [--enfase "#hex"] [--modo claro|escuro]
                  [--fonte-titulo "Nome"] [--fonte-texto "Nome"] [--saida-json caminho|-] [--gravar] [--verificar]
"""

from __future__ import annotations

import argparse
import colorsys
import json
import re
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
TEMAS_JSON = RAIZ / "temas.json"
MARCA_INICIO = "/* TEMAS:inicio */"
MARCA_FIM = "/* TEMAS:fim */"

# Pares (frente, fundo, mínimo). 4.5 = texto normal (WCAG 1.4.3 AA); 3.0 = texto
# grande ou elemento gráfico (1.4.11). No canvas 1600x900 o corpo tem >= 28px,
# mas rótulos e fontes de rodapé são menores: por isso o texto usa 4.5.
PARES = [
    ("texto", "fundo", 4.5),
    ("texto", "superficie", 4.5),
    ("texto", "primaria-suave", 4.5),
    ("texto", "codigo", 4.5),
    ("suave", "fundo", 4.5),
    ("suave", "superficie", 4.5),
    ("primaria", "fundo", 4.5),
    ("primaria", "superficie", 4.5),
    ("primaria", "primaria-suave", 4.5),
    ("sobre-primaria", "primaria", 4.5),
    ("enfase", "fundo", 4.5),
    ("enfase", "superficie", 4.5),
    ("ok", "fundo", 4.5),
    ("alerta", "fundo", 4.5),
    ("erro", "fundo", 4.5),
    ("cinza", "fundo", 1.8),  # série de contexto em gráfico: visível, mas recuada
    ("linha", "fundo", 1.15),  # fio de tabela: precisa existir
]
FALLBACK = {
    "titulo": '"Segoe UI", system-ui, sans-serif',
    "texto": '"Segoe UI", system-ui, sans-serif',
    "mono": 'ui-monospace, "Cascadia Mono", Consolas, monospace',
}
SERIFADAS = {"Source Serif 4"}


def carregar(caminho: Path = TEMAS_JSON) -> dict:
    return json.loads(caminho.read_text(encoding="utf-8"))


def hex_rgb(cor: str) -> tuple[float, float, float]:
    cor = cor.lstrip("#")
    if len(cor) == 3:
        cor = "".join(c * 2 for c in cor)
    if not re.fullmatch(r"[0-9a-fA-F]{6}", cor):
        raise ValueError(f"cor inválida: #{cor}")
    return tuple(int(cor[i : i + 2], 16) / 255 for i in (0, 2, 4))


def rgb_hex(rgb: tuple[float, float, float]) -> str:
    return "#" + "".join(f"{round(max(0.0, min(1.0, c)) * 255):02x}" for c in rgb)


def luminancia(cor: str) -> float:
    def canal(c: float) -> float:
        return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4

    r, g, b = (canal(c) for c in hex_rgb(cor))
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contraste(a: str, b: str) -> float:
    la, lb = sorted((luminancia(a), luminancia(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def pilha(familia: str, papel: str) -> str:
    fallback = FALLBACK[papel]
    if papel != "mono" and familia in SERIFADAS:
        fallback = 'Georgia, "Times New Roman", serif'
    return f'"{familia}", {fallback}'


def css(temas: dict, nomes: list[str] | None = None) -> str:
    nomes = nomes or list(temas)
    linhas = [MARCA_INICIO]
    for i, nome in enumerate(nomes):
        tema = temas[nome]
        seletor = f':root[data-tema="{nome}"]'
        if i == 0:
            seletor = f":root, {seletor}"
        linhas.append(f"{seletor} {{")
        for token, valor in tema["cores"].items():
            linhas.append(f"  --{token}: {valor};")
        for papel, familia in tema["fontes"].items():
            linhas.append(f"  --fonte-{papel}: {pilha(familia, papel)};")
        linhas.append(f"  color-scheme: {'dark' if tema['modo'] == 'escuro' else 'light'};")
        linhas.append("}")
    linhas.append(f':root {{ --temas: "{",".join(nomes)}"; }}')
    linhas.append(MARCA_FIM)
    return "\n".join(linhas)


def aplicar(arquivo: Path, temas: dict) -> None:
    texto = arquivo.read_text(encoding="utf-8")
    padrao = re.compile(re.escape(MARCA_INICIO) + r".*?" + re.escape(MARCA_FIM), re.S)
    if not padrao.search(texto):
        sys.exit(f"ERRO: {arquivo} não tem o bloco {MARCA_INICIO} ... {MARCA_FIM}")
    novo = padrao.sub(lambda _: css(temas), texto, count=1)
    lista = ",".join(temas)
    novo = re.sub(r'data-temas="[^"]*"', f'data-temas="{lista}"', novo, count=1)
    arquivo.write_text(novo, encoding="utf-8")
    print(f"temas aplicados em {arquivo}: {lista}")


def verificar(temas: dict, nomes: list[str]) -> bool:
    falhas = 0
    for nome in nomes:
        cores = temas[nome]["cores"]
        for frente, fundo, minimo in PARES:
            valor = contraste(cores[frente], cores[fundo])
            if valor < minimo:
                falhas += 1
                print(f"FALHA {nome}: {frente} sobre {fundo} = {valor:.2f} (mínimo {minimo})")
        print(f"{nome}: {len(PARES)} pares verificados")
    if falhas:
        print(f"CONTRASTE COM {falhas} FALHA(S)")
        return False
    print("CONTRASTE OK")
    return True


def ajustar(cor: str, fundo: str, minimo: float) -> str:
    """Escurece ou clareia mantendo matiz e saturação até atingir o contraste mínimo."""
    h, l, s = colorsys.rgb_to_hls(*hex_rgb(cor))
    escurecer = luminancia(fundo) > 0.4
    passo = -0.01 if escurecer else 0.01
    while contraste(rgb_hex(colorsys.hls_to_rgb(h, l, s)), fundo) < minimo and 0.0 < l < 1.0:
        l = min(1.0, max(0.0, l + passo))
    return rgb_hex(colorsys.hls_to_rgb(h, l, s))


def hls(h: float, l: float, s: float) -> str:
    return rgb_hex(colorsys.hls_to_rgb(h % 1.0, l, s))


def derivar(nome: str, primaria: str, enfase: str | None, modo: str, fonte_titulo: str, fonte_texto: str) -> dict:
    h, _, s = colorsys.rgb_to_hls(*hex_rgb(primaria))
    neutro = min(s, 0.18)  # neutros com leve viés para a matiz da marca
    if modo == "claro":
        fundo, superficie = hls(h, 0.975, neutro), "#ffffff"
        texto, suave = hls(h, 0.11, neutro + 0.1), hls(h, 0.38, neutro)
        linha, codigo, cinza = hls(h, 0.87, neutro), hls(h, 0.94, neutro), hls(h, 0.66, neutro * 0.6)
        prim = ajustar(primaria, superficie, 4.8)
        prim_suave = hls(h, 0.94, min(s, 0.45))
    else:
        fundo, superficie = hls(h, 0.07, neutro), hls(h, 0.11, neutro)
        texto, suave = hls(h, 0.95, neutro * 0.5), hls(h, 0.72, neutro)
        linha, codigo, cinza = hls(h, 0.22, neutro), hls(h, 0.05, neutro), hls(h, 0.42, neutro * 0.6)
        prim = ajustar(primaria, superficie, 4.8)
        prim_suave = hls(h, 0.16, min(s, 0.45))
    if enfase is None:  # matiz complementar deslocada, saturação moderada
        enfase = hls(h + 0.47, 0.42 if modo == "claro" else 0.62, 0.75)
    cores = {
        "fundo": fundo,
        "superficie": superficie,
        "texto": texto,
        "suave": ajustar(suave, superficie, 4.8),
        "linha": linha,
        "primaria": prim,
        "primaria-suave": prim_suave,
        "sobre-primaria": "#ffffff" if contraste("#ffffff", prim) >= contraste("#000000", prim) else "#000000",
        "enfase": ajustar(enfase, superficie, 4.8),
        "cinza": cinza,
        "ok": ajustar("#2f7d4f" if modo == "claro" else "#6cc28f", superficie, 4.8),
        "alerta": ajustar("#8f5a12" if modo == "claro" else "#e9b25c", superficie, 4.8),
        "erro": ajustar("#b42318" if modo == "claro" else "#f08a80", superficie, 4.8),
        "codigo": codigo,
    }
    # Garante os pares que dependem do fundo e da primaria-suave.
    for token in ("suave", "primaria", "enfase", "ok", "alerta", "erro"):
        cores[token] = ajustar(cores[token], cores["fundo"], 4.8)
    cores["primaria"] = ajustar(cores["primaria"], cores["primaria-suave"], 4.8)
    return {
        "rotulo": nome.capitalize(),
        "uso": f"Derivado da cor de marca {primaria}.",
        "modo": modo,
        "cores": cores,
        "fontes": {"titulo": fonte_titulo, "texto": fonte_texto, "mono": "IBM Plex Mono"},
    }


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("listar")
    p_css = sub.add_parser("css")
    p_css.add_argument("--temas")
    p_apl = sub.add_parser("aplicar")
    p_apl.add_argument("arquivo", type=Path)
    p_ver = sub.add_parser("verificar")
    p_ver.add_argument("--tema")
    p_ver.add_argument("--arquivo", type=Path, default=TEMAS_JSON)
    p_der = sub.add_parser("derivar")
    p_der.add_argument("--nome", required=True)
    p_der.add_argument("--primaria", required=True)
    p_der.add_argument("--enfase")
    p_der.add_argument("--modo", choices=("claro", "escuro"), default="claro")
    p_der.add_argument("--fonte-titulo", default="Space Grotesk")
    p_der.add_argument("--fonte-texto", default="IBM Plex Sans")
    p_der.add_argument("--saida-json", help="caminho do JSON do tema ou - para a saída padrão")
    p_der.add_argument("--gravar", action="store_true", help="acrescenta o tema em temas.json")
    p_der.add_argument("--verificar", action="store_true")
    a = ap.parse_args()

    if a.cmd == "listar":
        for nome, tema in carregar()["temas"].items():
            print(f"{nome:14} {tema['modo']:7} {tema['uso']}")
    elif a.cmd == "css":
        temas = carregar()["temas"]
        print(css(temas, a.temas.split(",") if a.temas else None))
    elif a.cmd == "aplicar":
        aplicar(a.arquivo, carregar()["temas"])
    elif a.cmd == "verificar":
        temas = carregar(a.arquivo)["temas"]
        sys.exit(0 if verificar(temas, [a.tema] if a.tema else list(temas)) else 1)
    elif a.cmd == "derivar":
        if not re.fullmatch(r"[a-z0-9-]+", a.nome):
            sys.exit("ERRO: --nome aceita só minúsculas, dígitos e hífen")
        tema = derivar(a.nome, a.primaria, a.enfase, a.modo, a.fonte_titulo, a.fonte_texto)
        if a.saida_json == "-":
            print(json.dumps({a.nome: tema}, ensure_ascii=False, indent=2))
        elif a.saida_json:
            Path(a.saida_json).write_text(json.dumps({a.nome: tema}, ensure_ascii=False, indent=2), encoding="utf-8")
        if a.gravar:
            dados = carregar()
            dados["temas"][a.nome] = tema
            TEMAS_JSON.write_text(json.dumps(dados, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            print(f"tema {a.nome} gravado em {TEMAS_JSON}")
        if a.verificar:
            sys.exit(0 if verificar({a.nome: tema}, [a.nome]) else 1)


if __name__ == "__main__":
    main()
