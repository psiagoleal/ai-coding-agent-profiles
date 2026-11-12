#!/usr/bin/env python3
# Caminho relativo: skills/dominio/checagem-fatos/scripts/checar-relatorio.py
"""Valida a tabela de alegações de um relatório de checagem de fatos.

    checar-relatorio.py <relatorio.md> [...]
    checar-relatorio.py --autoteste

Reprova (código 1), por linha da tabela:
  - classificação fora da escala (Verdadeiro, Impreciso, Distorcido, Falso, Insustentável, Opinião);
  - "Informação correta" vazia;
  - nenhuma referência com link, exceto em Opinião;
  - referência com link sem etiqueta [O] (oficial) ou [N] (não oficial) no início;
  - nenhuma referência [O] sem declarar "Sem fonte oficial localizada" (exceto Opinião).
Reprova também o arquivo sem tabela com as colunas Classificação, Informação correta e Referências.
Só biblioteca padrão, sem rede.
"""
from __future__ import annotations

import re
import sys
import tempfile
from pathlib import Path

ESCALA = ("Verdadeiro", "Impreciso", "Distorcido", "Falso", "Insustentável", "Opinião")
COLUNAS = ("classificação", "informação correta", "referências")
SEM_OFICIAL = "sem fonte oficial localizada"
LINK = re.compile(r"\]\(\s*https?://")
SEPARADOR = re.compile(r"^\|?\s*:?-{3,}")


def celulas(linha: str) -> list[str]:
    s = linha.strip()
    if s.startswith("|"):
        s = s[1:]
    if s.endswith("|"):
        s = s[:-1]
    return [c.strip() for c in s.split("|")]


def checar_texto(texto: str) -> list[str]:
    erros: list[str] = []
    linhas = texto.splitlines()
    achou_tabela = False
    i = 0
    while i < len(linhas):
        cab = linhas[i]
        if cab.lstrip().startswith("|") and i + 1 < len(linhas) and SEPARADOR.match(linhas[i + 1].strip()):
            nomes = [c.lower() for c in celulas(cab)]
            idx = {}
            for col in COLUNAS:
                pos = [k for k, n in enumerate(nomes) if n.startswith(col)]
                if pos:
                    idx[col] = pos[0]
            if len(idx) == len(COLUNAS):
                achou_tabela = True
                j = i + 2
                while j < len(linhas) and linhas[j].lstrip().startswith("|"):
                    erros += checar_linha(celulas(linhas[j]), idx, j + 1)
                    j += 1
                i = j
                continue
        i += 1
    if not achou_tabela:
        erros.append("nenhuma tabela com as colunas Classificação, Informação correta e Referências")
    return erros


def checar_linha(c: list[str], idx: dict[str, int], n: int) -> list[str]:
    erros: list[str] = []
    if len(c) <= max(idx.values()):
        return [f"linha {n}: número de colunas menor que o cabeçalho"]
    classe, info, refs = (c[idx[k]] for k in COLUNAS)
    rotulos = [r for r in ESCALA if r.lower() in classe.lower()]
    if len(rotulos) != 1:
        erros.append(f"linha {n}: classificação '{classe}' fora da escala {ESCALA}")
    opiniao = rotulos == ["Opinião"]
    if not info or info in ("—", "-"):
        erros.append(f"linha {n}: 'Informação correta' vazia")
    pedacos = [p.strip() for p in re.split(r"<br\s*/?>|;", refs) if p.strip() and p.strip() not in ("—", "-")]
    com_link = [p for p in pedacos if LINK.search(p)]
    if not com_link and not opiniao:
        erros.append(f"linha {n}: sem referência com link")
    for p in com_link:
        if not re.match(r"^\*{0,2}\[(O|N)\]", p):
            erros.append(f"linha {n}: referência sem etiqueta [O]/[N]: {p[:60]}")
    tem_oficial = any(re.match(r"^\*{0,2}\[O\]", p) for p in com_link)
    if com_link and not tem_oficial and not opiniao and SEM_OFICIAL not in info.lower():
        erros.append(f"linha {n}: só referências [N] — declare '{SEM_OFICIAL.capitalize()}' em Informação correta")
    return erros


CAB = "| # | Alegação | Classificação | Informação correta | Referências |\n|---|---|---|---|---|\n"
CASOS = [
    ("válido completo",
     CAB + "| 1 | a | ✅ Verdadeiro | x | [O] [FCC](https://fcc.gov) |\n"
           "| 2 | b | ❔ Insustentável | Sem fonte oficial localizada. y | [N] [G1](https://g1.globo.com) |\n"
           "| 3 | c | 💬 Opinião | especulação | — |\n", 0),
    ("sem tabela", "# título\n\ntexto\n", 1),
    ("classificação fora da escala", CAB + "| 1 | a | Meio certo | x | [O] [A](https://a.gov) |\n", 1),
    ("informação correta vazia", CAB + "| 1 | a | ✅ Verdadeiro |  | [O] [A](https://a.gov) |\n", 1),
    ("sem referência", CAB + "| 1 | a | ❌ Falso | x | — |\n", 1),
    ("referência sem etiqueta", CAB + "| 1 | a | ❌ Falso | x | [A](https://a.gov) |\n", 1),
    ("só [N] sem declarar", CAB + "| 1 | a | ✅ Verdadeiro | x | [N] [A](https://a.com) |\n", 1),
    ("mistura O e N", CAB + "| 1 | a | 🟠 Distorcido | x | [N] [A](https://a.com)<br>[O] [B](https://b.gov) |\n", 0),
    ("segunda ref sem etiqueta", CAB + "| 1 | a | 🟡 Impreciso | x | [O] [A](https://a.gov)<br>[B](https://b.com) |\n", 1),
]


def autoteste() -> int:
    falhas = 0
    with tempfile.TemporaryDirectory() as d:
        for nome, texto, esperado in CASOS:
            p = Path(d) / "r.md"
            p.write_text(texto, encoding="utf-8")
            obtido = 1 if checar_texto(p.read_text(encoding="utf-8")) else 0
            ok = obtido == esperado
            falhas += not ok
            print(f"{'ok  ' if ok else 'FALHA'} {nome}: esperado {esperado}, obtido {obtido}")
    print(f"{len(CASOS) - falhas}/{len(CASOS)} casos")
    return 1 if falhas else 0


def main(args: list[str]) -> int:
    if args == ["--autoteste"]:
        return autoteste()
    if not args or any(a.startswith("-") for a in args):
        print(__doc__, file=sys.stderr)
        return 2
    total = 0
    for a in args:
        erros = checar_texto(Path(a).read_text(encoding="utf-8"))
        for e in erros:
            print(f"{a}: {e}")
        total += len(erros)
        if not erros:
            print(f"{a}: ok")
    return 1 if total else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
