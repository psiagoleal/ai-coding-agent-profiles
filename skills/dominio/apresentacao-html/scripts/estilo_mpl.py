"""Estilo de gráfico matplotlib/schemdraw a partir de temas.json.

Uso em um script de figura (rodar com `py`, ver ambiente.sh):

    import sys; sys.path.insert(0, "<skill>/scripts")
    import estilo_mpl
    cores = estilo_mpl.aplicar("tecnico")       # define rcParams e devolve as cores
    ...
    estilo_mpl.salvar(fig, "saida/grafico.svg")  # SVG transparente, texto como texto

Regras de dado embutidas: fundo transparente (herda o slide), cinza para contexto
e uma cor de ênfase para a mensagem, sem moldura superior/direita, grade leve.
Gere a figura com o MESMO tema inicial do deck: construir.mjs troca essas cores
por variáveis CSS quando a imagem usa `data-inline`, e a figura acompanha a troca
de tema na apresentação.
"""

from __future__ import annotations

import json
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent


def cores(tema: str = "tecnico") -> dict:
    dados = json.loads((RAIZ / "temas.json").read_text(encoding="utf-8"))
    t = dados["temas"][tema]
    return {**t["cores"], "_fontes": t["fontes"]}


def aplicar(tema: str = "tecnico", tamanho: float = 16) -> dict:
    import matplotlib

    matplotlib.use("Agg")
    from cycler import cycler
    from matplotlib import rcParams

    c = cores(tema)
    rcParams.update(
        {
            "font.family": "sans-serif",
            "font.sans-serif": [c["_fontes"]["texto"], "DejaVu Sans"],
            "font.size": tamanho,
            "text.color": c["texto"],
            "axes.labelcolor": c["suave"],
            "axes.edgecolor": c["linha"],
            "axes.facecolor": "none",
            "figure.facecolor": "none",
            "savefig.facecolor": "none",
            "axes.spines.top": False,
            "axes.spines.right": False,
            "axes.grid": False,
            "grid.color": c["linha"],
            "grid.linewidth": 0.8,
            "xtick.color": c["suave"],
            "ytick.color": c["suave"],
            "axes.titleweight": "semibold",
            "axes.titlesize": tamanho * 1.15,
            "axes.titlelocation": "left",
            "axes.prop_cycle": cycler(color=[c["primaria"], c["cinza"], c["enfase"], c["suave"]]),
            "lines.linewidth": 2.4,
            "svg.fonttype": "none",  # texto continua texto: usa a fonte embutida no deck
            "legend.frameon": False,
        }
    )
    return c


def salvar(fig, caminho: str | Path) -> Path:
    caminho = Path(caminho)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(caminho, transparent=True, bbox_inches="tight", pad_inches=0.1)
    return caminho


def schemdraw_config(tema: str = "tecnico", tamanho: float = 14) -> dict:
    """Configura o schemdraw (backend SVG próprio) com as cores do tema."""
    import schemdraw

    c = cores(tema)
    schemdraw.use("svg")
    schemdraw.config(color=c["texto"], bgcolor="none", font=c["_fontes"]["texto"], fontsize=tamanho, lw=2)
    schemdraw.svgconfig.text = "text"  # mantém texto como texto no SVG
    return c
