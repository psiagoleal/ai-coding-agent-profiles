#!/usr/bin/env python3
# Caminho relativo: skills/dominio/exercicio-resolvido/scripts/passo.py
"""Fórmula → substituição → resultado, na ordem, com sympy.

A convenção é mecânica de propósito: quem lê precisa ver a conta, não só o número.
Importe no notebook (`from passo import mostrar`) ou copie a função.

    >>> import sympy as sp
    >>> G_L, G_S = sp.symbols('G_L G_S', positive=True)
    >>> mostrar('\\eta', G_L/(G_S+G_L), {G_L: 0.0533, G_S: 0.01333}, unidade='')

Fora do notebook, imprime em texto; dentro, renderiza em LaTeX pelo IPython.
"""
from __future__ import annotations

import sympy as sp


def _exibir(latex: str, texto: str) -> None:
    try:  # notebook
        from IPython.display import Math, display
        display(Math(latex))
    except Exception:  # script, terminal, nbconvert sem IPython
        print(texto)


def mostrar(rotulo: str, expr, valores: dict | None = None, unidade: str = "",
            casas: int = 4, simplificar: bool = False):
    """Exibe as três linhas e devolve o valor numérico (ou a expressão, sem valores).

    O valor devolvido tem **precisão cheia**; `casas` afeta apenas o que aparece na tela.
    Encadeie sempre o retorno, nunca o número que você leu no notebook.

    rotulo  — nome da grandeza em LaTeX, sem cifrões (ex.: 'P_L', r'\\eta')
    expr    — expressão sympy com os símbolos
    valores — {simbolo: valor}; sem isso, só a fórmula é mostrada
    """
    if simplificar:
        expr = sp.simplify(expr)

    # (a) fórmula, com os símbolos
    _exibir(f"{rotulo} = {sp.latex(expr)}", f"{rotulo} = {expr}")
    if not valores:
        return expr

    faltando = sorted(str(s) for s in expr.free_symbols - set(valores))
    if faltando:
        raise ValueError(f"sem valor para: {', '.join(faltando)} — a substituição ficaria pela metade")

    # (b) substituição, SEM avaliar: é o passo que o aluno confere
    congelado = expr.subs({k: sp.UnevaluatedExpr(v) for k, v in valores.items()})
    _exibir(f"{rotulo} = {sp.latex(congelado)}", f"{rotulo} = {congelado}")

    # (c) resultado numérico, com unidade.
    # O ARREDONDAMENTO É SÓ DA EXIBIÇÃO. O que volta tem precisão cheia, porque encadear
    # passos com o número arredondado propaga o erro e faz a verificação final fechar
    # "quase" — o aluno conclui que o projeto está impreciso quando o impreciso era o print.
    exato = sp.N(expr.subs(valores))
    mostrado = sp.N(exato, casas)
    suf = f"\\ \\mathrm{{{unidade}}}" if unidade else ""
    _exibir(f"{rotulo} = {sp.latex(mostrado)}{suf}", f"{rotulo} = {mostrado} {unidade}".rstrip())
    return exato


def _teste_encadeamento() -> None:
    """O retorno tem de ter precisão cheia: encadear o número arredondado propaga erro.

    Retorno de campo (2026-09-23): a verificação final fechava com resíduo de 3e-5 no
    notebook e zero no script — o impreciso era a exibição, não o projeto.
    """
    import math

    R, X = sp.symbols("R X", positive=True)
    q = mostrar("Q", sp.sqrt(R / X - 1), {R: 75.0, X: 12.3}, casas=4)
    erro = abs(float(q) - math.sqrt(75.0 / 12.3 - 1))
    assert erro < 1e-12, f"retorno veio arredondado: erro {erro:g}"
    print(f"encadeamento ok — erro do retorno: {erro:g} (a exibição segue em 4 casas)")


if __name__ == "__main__":  # autoteste: python3 passo.py
    I_S, G_L, G_S, B_S, B_L = sp.symbols("I_S G_L G_S B_S B_L", real=True)
    P_L = I_S**2 * G_L / (2 * ((G_S + G_L) ** 2 + (B_S + B_L) ** 2))
    mostrar("P_L", P_L, {I_S: 0.08, G_L: sp.Rational(1, 75), G_S: sp.Rational(1, 75),
                         B_S: -0.005526, B_L: 0.005526}, unidade="W")
    mostrar(r"\eta", G_L / (G_S + G_L), {G_L: sp.Rational(1, 75), G_S: sp.Rational(1, 75)})
    _teste_encadeamento()

