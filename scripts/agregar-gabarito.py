#!/usr/bin/env python3
# Caminho relativo: scripts/agregar-gabarito.py
"""Agrega a trilha de decisão (JSONL) nas três medidas do plano de decisão tipada.

    agregar-gabarito.py <audit.jsonl>... [--rotulos <arq.jsonl>] [--padrao <task-class>] [--json]

Mede, nesta ordem:

  1. **Acerto contra o baseline trivial** — o baseline é mandar tudo para uma única
     task-class. Roteador que não ganha dele não se adota.
  2. **Calibração** — entre as decisões com confiança em cada faixa, quantas acertaram.
     Só existe quando o roteador é probabilístico; roteamento declarado não tem o campo.
  3. **Custo** — sobrecarga do roteador (`decision_ms`) e distribuição de classe de egresso,
     mais o que hoje é queda silenciosa: candidatos descartados, por motivo.

Verdade de referência, em ordem de preferência:
  a) arquivo de rótulos (`--rotulos`), uma linha por decisão: {"i": <índice>, "correto": "<classe>"};
  b) na ausência dele, **escalada como sinal**: rota seguida de `kind=escalation` conta como
     decisão que não se sustentou. É proxy, não verdade — está dito no relatório.

Compatibilidade: linha **sem** `kind` é de egresso (formato anterior à trilha) e é contada,
não descartada. `profile` vem como nome de variante e `egress_class` em kebab — a
inconsistência é da origem e não se normaliza aqui, para o relatório não mentir sobre o dado.

Códigos: 0 relatório emitido · 1 nenhuma linha de rota · 2 uso ou arquivo ilegível.
"""
from __future__ import annotations

import argparse
import json
import sys
from collections import Counter, defaultdict
from pathlib import Path

FAIXAS = [(0.0, 0.5), (0.5, 0.7), (0.7, 0.8), (0.8, 0.9), (0.9, 1.01)]


def carregar(caminhos: list[Path]) -> tuple[list[dict], int]:
    linhas, malformadas = [], 0
    for c in caminhos:
        try:
            texto = c.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            sys.exit(f"não consegui ler {c}: {e}")
        for bruta in texto.splitlines():
            bruta = bruta.strip()
            if not bruta:
                continue
            try:
                d = json.loads(bruta)
            except json.JSONDecodeError:
                malformadas += 1
                continue
            if isinstance(d, dict):
                # Linha sem 'kind' é de egresso: formato anterior à trilha, mantido por
                # compatibilidade. Tratar como desconhecida descartaria histórico real.
                d.setdefault("kind", "egress")
                linhas.append(d)
    return linhas, malformadas


def verdade(rotas: list[dict], rotulos: dict[int, str], linhas: list[dict]) -> tuple[list[bool | None], str]:
    """→ (acertos por rota, origem da verdade). None = sem verdade para aquela rota."""
    if rotulos:
        return [rotulos.get(r["_i"]) == r.get("task_class") if r["_i"] in rotulos else None
                for r in rotas], "rótulos"
    # Proxy: uma escalada logo após a rota indica decisão que não se sustentou.
    escaladas = {l["_i"] for l in linhas if l.get("kind") == "escalation"}
    acertos: list[bool | None] = []
    for r in rotas:
        prox = [i for i in escaladas if i > r["_i"]]
        seguinte = min(prox) if prox else None
        outra_rota = [o["_i"] for o in rotas if o["_i"] > r["_i"]]
        limite = min(outra_rota) if outra_rota else float("inf")
        acertos.append(not (seguinte is not None and seguinte < limite))
    return acertos, "escalada como proxy"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("arquivos", nargs="+", type=Path)
    ap.add_argument("--rotulos", type=Path)
    ap.add_argument("--padrao", help="task-class do baseline trivial (padrão: a mais frequente)")
    ap.add_argument("--json", action="store_true")
    a = ap.parse_args()

    linhas, malformadas = carregar(a.arquivos)
    for i, l in enumerate(linhas):
        l["_i"] = i
    rotas = [l for l in linhas if l.get("kind") == "route"]
    if not rotas:
        print("nenhuma linha 'kind=route' — nada a medir (a trilha já existe?)", file=sys.stderr)
        return 1

    rotulos: dict[int, str] = {}
    if a.rotulos:
        for bruta in a.rotulos.read_text(encoding="utf-8").splitlines():
            if bruta.strip():
                d = json.loads(bruta)
                rotulos[int(d["i"])] = d["correto"]

    acertos, origem = verdade(rotas, rotulos, linhas)
    com_verdade = [(r, ok) for r, ok in zip(rotas, acertos) if ok is not None]

    classes = Counter(r.get("task_class", "?") for r in rotas)
    padrao = a.padrao or (classes.most_common(1)[0][0] if classes else "?")
    # Baseline trivial: mandar tudo para uma única task-class. É o número a bater.
    base_ok = sum(1 for r, ok in com_verdade
                  if (rotulos.get(r["_i"]) or r.get("task_class")) == padrao)
    rot_ok = sum(1 for _, ok in com_verdade if ok)
    n = len(com_verdade)

    # Calibração: só existe se o roteador emitir confiança.
    faixas: dict[tuple[float, float], list[bool]] = defaultdict(list)
    for r, ok in com_verdade:
        c = r.get("confidence")
        if isinstance(c, (int, float)):
            for lo, hi in FAIXAS:
                if lo <= c < hi:
                    faixas[(lo, hi)].append(bool(ok))
                    break
    ece = sum(len(v) / n * abs(sum(v) / len(v) - (lo + hi) / 2)
              for (lo, hi), v in faixas.items() if v) if faixas and n else None

    descartes = Counter(d.get("reason", "?") for r in rotas for d in r.get("discarded", []))
    ms = [r["decision_ms"] for r in rotas if isinstance(r.get("decision_ms"), (int, float))]
    egressos = Counter(r.get("chosen", {}).get("egress_class", "?") for r in rotas)
    sem_at = sum(1 for r in rotas if "at" not in r)

    dados = {
        "linhas": len(linhas), "malformadas": malformadas,
        "rotas": len(rotas), "com_verdade": n, "origem_da_verdade": origem,
        "baseline": {"task_class": padrao, "acerto": round(base_ok / n, 4) if n else None},
        "roteador": {"acerto": round(rot_ok / n, 4) if n else None},
        "ganho_sobre_baseline": round((rot_ok - base_ok) / n, 4) if n else None,
        "calibracao": {"faixas": {f"{lo}-{hi}": {"n": len(v), "acerto": round(sum(v) / len(v), 4)}
                                  for (lo, hi), v in sorted(faixas.items()) if v},
                       "erro_esperado": round(ece, 4) if ece is not None else None},
        "custo": {"decision_ms_p50": sorted(ms)[len(ms) // 2] if ms else None,
                  "decision_ms_total": sum(ms) if ms else None,
                  "rotas_sem_decision_ms": len(rotas) - len(ms)},
        "descartes_por_motivo": dict(descartes),
        "egresso_escolhido": dict(egressos),
        "rotas_sem_timestamp": sem_at,
        "por_task_class": dict(classes),
    }

    if a.json:
        print(json.dumps(dados, ensure_ascii=False, indent=1))
        return 0

    d = dados
    print(f"\n\033[1mGabarito\033[0m — {d['rotas']} rota(s) em {d['linhas']} linha(s)"
          + (f", {malformadas} malformada(s)" if malformadas else ""))
    print(f"  verdade de referência: {origem} ({n} rota(s) com verdade)")
    if n:
        print(f"\n  baseline trivial (tudo para '{padrao}'): {d['baseline']['acerto']:.1%}")
        print(f"  roteador:                               {d['roteador']['acerto']:.1%}")
        g = d["ganho_sobre_baseline"]
        print(f"  \033[1mganho sobre o baseline: {g:+.1%}\033[0m"
              + ("  — roteador não se paga" if g <= 0 else ""))
    if d["calibracao"]["faixas"]:
        print("\n  calibração (confiança → acerto observado):")
        for faixa, v in d["calibracao"]["faixas"].items():
            print(f"    {faixa:>9}  n={v['n']:<5} acerto={v['acerto']:.1%}")
        print(f"    erro esperado de calibração: {d['calibracao']['erro_esperado']:.4f}")
    else:
        print("\n  calibração: \033[33mindisponível\033[0m — nenhuma rota traz 'confidence'"
              " (roteamento declarado não tem probabilidade)")
    c = d["custo"]
    if c["decision_ms_p50"] is not None:
        print(f"\n  sobrecarga do roteador: mediana {c['decision_ms_p50']} ms,"
              f" total {c['decision_ms_total']} ms")
    else:
        print("\n  sobrecarga do roteador: \033[33mindisponível\033[0m — nenhuma rota traz"
              " 'decision_ms'")
    if d["descartes_por_motivo"]:
        print(f"  descartes por motivo: {d['descartes_por_motivo']}"
              "   ← o que hoje cairia em silêncio")
    print(f"  egresso escolhido: {d['egresso_escolhido']}")
    if sem_at:
        print(f"  \033[33m{sem_at} rota(s) sem 'at'\033[0m: duração entre linhas não é derivável")
    print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
