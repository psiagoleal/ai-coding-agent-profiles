#!/usr/bin/env python3
# Caminho relativo: skills/micro-ticket-planner/scripts/checar-painel.py
"""Confere o painel de tickets contra a convenção fechada de marcadores.

    checar-painel.py [docs/TICKETS.md] [--limite-urgentes 3]

Verifica: marcador dentro do conjunto fechado, marcador compatível com a seção, link para o
detalhe, `[>]` dizendo o que falta, `[~]` com motivo, e o teto de `[!]`.

Códigos: 0 painel válido · 1 problema encontrado · 2 arquivo ausente ou sem seções.
A convenção está em skills/micro-ticket-planner/SKILL.md.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

MARCADORES = {" ": "em aberto", ">": "em andamento", "!": "urgente", "x": "concluído",
              "~": "abandonado ou recusado"}
# `Recusados` é a quarta seção, criada pela ADR 0019: recusa disfarçada de abandono é recusa
# que volta. Divide o marcador `[~]` com `Abandonados`, e a seção é que diz qual dos dois.
SECAO_DE = {"em aberto": {" ", ">", "!"}, "concluídos": {"x"}, "abandonados": {"~"},
            "recusados": {"~"}}
# Exigidas em todo painel. `Recusados` fica FORA: painel já instalado em outro projeto não a
# tem, e torná-la obrigatória reprovaria o painel alheio por uma decisão nossa. Quem a usa,
# usa verificada; quem não a usa não é reprovado.
SECOES_EXIGIDAS = {"em aberto", "concluídos", "abandonados"}
LINHA = re.compile(r"^\s*-\s*\[(.)\]\s*(.*)$")
LINK = re.compile(r"\[[^\]]+\]\([^)]+\)")
# A ADR 0019 pede que a linha de recusa cite a ADR ou o arquivo em `docs/recusados/`. Sem
# isto a seção entraria sem exame, que é o defeito do MT-41 aplicado a ela mesma.
FONTE_DA_RECUSA = re.compile(r"\]\(([^)]*(?:recusados/|adr/)[^)]*)\)")


def normalizar(titulo: str) -> str:
    return titulo.strip().lower().rstrip(":")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("painel", nargs="?", default="docs/TICKETS.md")
    ap.add_argument("--limite-urgentes", type=int, default=3)
    a = ap.parse_args()

    arq = Path(a.painel)
    if not arq.is_file():
        print(f"painel não encontrado: {arq}", file=sys.stderr)
        return 2

    problemas: list[str] = []
    urgentes: list[str] = []
    secao = ""
    vistas: set[str] = set()
    tickets = 0

    for n, linha in enumerate(arq.read_text(encoding="utf-8").splitlines(), 1):
        if linha.startswith("##"):
            secao = normalizar(linha.lstrip("#"))
            vistas.add(secao)
            continue
        if linha.lstrip().startswith("<!--"):  # exemplo comentado do template
            continue
        m = LINHA.match(linha)
        if not m:
            continue
        marcador, resto = m.group(1), m.group(2).strip()
        tickets += 1
        onde = f"{arq}:{n}"

        if marcador not in MARCADORES:
            problemas.append(f"{onde}: marcador '[{marcador}]' fora do conjunto fechado "
                             f"({', '.join('[' + k + ']' for k in MARCADORES)})")
            continue
        esperado = SECAO_DE.get(secao)
        if esperado and marcador not in esperado:
            problemas.append(f"{onde}: '[{marcador}]' ({MARCADORES[marcador]}) na seção '{secao}'")
        if not LINK.search(resto):
            problemas.append(f"{onde}: sem link para o detalhe — painel sem link é índice que mente")
        if marcador == "!":
            urgentes.append(onde)
        if marcador == ">" and not re.search(r"falta|restam?|pendente", resto, re.I):
            problemas.append(f"{onde}: '[>]' sem dizer o que falta — sem isso é '[ ]' com enfeite")
        # Fora do link: o texto do link pode conter a palavra "motivo" e passar por motivo.
        # Medido em 2026-10-13, com painel fabricado.
        fora_do_link = LINK.sub("", resto).lower()
        if marcador == "~" and "motivo" not in fora_do_link:
            problemas.append(f"{onde}: '[~]' sem motivo — o abandonado também é história")
        if secao == "recusados" and not FONTE_DA_RECUSA.search(resto):
            problemas.append(f"{onde}: recusa sem citar a ADR nem o arquivo em docs/recusados/ "
                             f"— recusa sem fonte é recusa que volta")

    faltando = SECOES_EXIGIDAS - vistas
    if faltando:
        print(f"{arq}: sem as seções {', '.join(sorted(faltando))}", file=sys.stderr)
        return 2

    if len(urgentes) > a.limite_urgentes:
        problemas.append(f"{len(urgentes)} tickets '[!]' (máximo {a.limite_urgentes}): "
                         f"se tudo é urgente, nada é — repriorize. Em: "
                         + ", ".join(u.split(':')[-1] for u in urgentes))

    if problemas:
        print(f"painel com {len(problemas)} problema(s):", file=sys.stderr)
        for p in problemas:
            print(f"  - {p}", file=sys.stderr)
        return 1

    print(f"painel válido: {tickets} ticket(s), {len(urgentes)} urgente(s)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
