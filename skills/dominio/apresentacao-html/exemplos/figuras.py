"""Gera as figuras do deck de exemplo: unifilar (schemdraw), gráfico de barras e
diagrama fasorial (matplotlib). Dados fictícios.

Uso: source scripts/ambiente.sh && py exemplos/figuras.py <pasta-saida> [--tema tecnico]
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import estilo_mpl  # noqa: E402


def unifilar(saida: Path, tema: str) -> Path:
    import schemdraw
    import schemdraw.elements as elm
    from schemdraw.segments import Segment, SegmentCircle

    c = estilo_mpl.schemdraw_config(tema)

    class Disjuntor(elm.Element2Term):
        """Disjuntor em diagrama unifilar: quadrado no eixo do circuito."""

        def __init__(self, **kw):
            super().__init__(**kw)
            a = 0.32
            self.segments.append(Segment([(0, 0), (0, a), (2 * a, a), (2 * a, -a), (0, -a), (0, 0)]))

    class Trafo(elm.Element2Term):
        """Transformador de dois enrolamentos: dois círculos sobrepostos."""

        def __init__(self, **kw):
            super().__init__(**kw)
            r = 0.42
            self.segments.append(Segment([(0, 0), (0, 0)]))
            self.segments.append(SegmentCircle((r, 0), r))
            self.segments.append(SegmentCircle((r * 2.3, 0), r))
            self.segments.append(Segment([(r * 3.3, 0), (r * 3.3, 0)]))

    def barra(d, rotulo):
        b = d.add(elm.Line().right(5).linewidth(6).color(c["primaria"]))
        d.add(elm.Label().at(b.start).label(rotulo, loc="left", ofst=0.3, color=c["primaria"]))
        return b

    with schemdraw.Drawing(show=False) as d:
        d.config(unit=2.2)
        b1 = barra(d, "500 kV")
        d.move_from(b1.center, dx=0, dy=0)
        d.add(elm.Line().down(0.6))
        d.add(Disjuntor().down().label("52-1", loc="bottom", ofst=(0.8, 0)))
        t1 = d.add(Trafo().down())
        # Rótulo posicionado à mão: folga fixa à direita dos círculos.
        d.add(elm.Label().at((t1.center[0] + 1.0, t1.center[1])).label("T1  500/230 kV\n3 × 200 MVA", halign="left"))
        d.add(Disjuntor().down().label("52-2", loc="bottom", ofst=(0.8, 0)))
        fim = d.add(elm.Line().down(0.6))
        d.move_from(fim.end, dx=-2.5, dy=0)
        b2 = barra(d, "230 kV")
        d.move_from(b2.end, dx=-1.0, dy=0)
        d.add(elm.Line().down(0.6))
        d.add(Disjuntor().down().label("52-3", loc="bottom", ofst=(0.8, 0)))
        d.add(elm.Arrow().down(1.2).label("LT 230 kV", loc="bottom", ofst=(1.2, 0)))
    caminho = saida / "unifilar.svg"
    caminho.write_bytes(d.get_imagedata("svg"))
    return caminho


def barras(saida: Path, tema: str) -> Path:
    import matplotlib.pyplot as plt

    c = estilo_mpl.aplicar(tema)
    categorias = ["Transformadores", "Equipamentos de pátio", "Cabos", "Estruturas", "Serviços"]
    valores = [184, 96, 71, 43, 18]  # fictícios, R$ milhões
    fig, ax = plt.subplots(figsize=(9, 4.6))
    cores_barras = [c["enfase"]] + [c["cinza"]] * (len(valores) - 1)
    barras_ = ax.barh(categorias[::-1], valores[::-1], color=cores_barras[::-1], height=0.62)
    for b, v in zip(barras_, valores[::-1]):
        ax.text(b.get_width() + 3, b.get_y() + b.get_height() / 2, f"{v}", va="center", color=c["texto"])
    ax.set_xlabel("CAPEX estimado (R$ milhões)")
    ax.spines["left"].set_visible(False)
    ax.tick_params(axis="y", length=0)
    ax.set_xlim(0, max(valores) * 1.15)
    # Sem título nem fonte no gráfico: o título-afirmação e a fonte ficam no slide.
    return estilo_mpl.salvar(fig, saida / "barras.svg")


def fasorial(saida: Path, tema: str) -> Path:
    import matplotlib.pyplot as plt
    from matplotlib.patches import Arc

    c = estilo_mpl.aplicar(tema)
    fig, ax = plt.subplots(figsize=(6.4, 5))
    phi = math.radians(-30)
    v, i, xi = 1.0, 0.75, 0.35
    seta = dict(arrowstyle="-|>", lw=2.6, mutation_scale=22)
    ax.annotate("", xy=(v, 0), xytext=(0, 0), arrowprops={**seta, "color": c["primaria"]})
    ax.annotate("", xy=(i * math.cos(phi), i * math.sin(phi)), xytext=(0, 0), arrowprops={**seta, "color": c["enfase"]})
    # Queda na reatância: jX·I, perpendicular a I, a partir da ponta de V.
    dx, dy = xi * math.cos(phi + math.pi / 2), xi * math.sin(phi + math.pi / 2)
    ax.annotate("", xy=(v + dx, dy), xytext=(v, 0),
                arrowprops={**seta, "color": c["suave"], "lw": 2, "linestyle": "--", "shrinkB": 9})
    ax.annotate("", xy=(v + dx, dy), xytext=(0, 0), arrowprops={**seta, "color": c["texto"]})
    ax.add_patch(Arc((0, 0), 0.5, 0.5, theta1=-30, theta2=0, color=c["suave"], lw=1.5))
    ax.text(0.3, -0.07, "φ", color=c["suave"])
    ax.text(v + 0.02, -0.08, r"$\dot V_2$", color=c["primaria"])
    ax.text(i * math.cos(phi), i * math.sin(phi) - 0.1, r"$\dot I$", color=c["enfase"])
    ax.text(v + dx / 2 + 0.07, dy / 2 - 0.02, r"$jX\dot I$", color=c["suave"])
    ax.text(v + dx - 0.05, dy + 0.06, r"$\dot V_1$", color=c["texto"])
    ax.set_aspect("equal")
    ax.set_xlim(-0.1, 1.45)
    ax.set_ylim(-0.55, 0.55)
    ax.axis("off")
    return estilo_mpl.salvar(fig, saida / "fasorial.svg")


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("saida", type=Path)
    ap.add_argument("--tema", default="tecnico")
    a = ap.parse_args()
    a.saida.mkdir(parents=True, exist_ok=True)
    for f in (unifilar, barras, fasorial):
        caminho = f(a.saida, a.tema)
        print(f"gerado {caminho} ({caminho.stat().st_size} bytes)")
    print("FIGURAS OK")


if __name__ == "__main__":
    main()
