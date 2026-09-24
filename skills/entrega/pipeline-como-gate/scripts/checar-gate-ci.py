#!/usr/bin/env python3
# Caminho relativo: skills/entrega/pipeline-como-gate/scripts/checar-gate-ci.py
"""Confere se o CI roda os mesmos comandos que o AGENTS.md declara.

    checar-gate-ci.py [--agents AGENTS.md] [--workflows .github/workflows]

Lê a ilha `USER:BEGIN id=comandos-exatos` do AGENTS.md, extrai os comandos do bloco de
código e procura cada um nos `run:` dos workflows. Também aponta os afrouxamentos que
transformam gate em enfeite: `continue-on-error`, `|| true`, job sem `timeout-minutes`,
`pull_request_target` e *action* em `@main`/`@master`.

Comparação por **ferramenta e verbo** (ex.: `cargo test`, `pytest`, `ruff check`), não por
texto literal: o CI costuma acrescentar `--all-features`, `-q` ou caminho. Por isso é um
alarme de divergência, não uma prova de equivalência — leia o que ele apontar.

Códigos: 0 sem divergência · 1 divergência encontrada · 2 arquivo ausente.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

ILHA = re.compile(r"USER:BEGIN\s+id=comandos-exatos(.*?)USER:END", re.S)
CODIGO = re.compile(r"```(?:bash|sh|shell)?\n(.*?)```", re.S)
# Comando "significativo": ferramenta + verbo. Ignora cd, export, echo e afins.
IGNORAR = {"cd", "export", "echo", "source", ".", "set", "ls", "mkdir", "cp", "mv", "rm", "free"}


def comandos_da_linha(linha: str) -> list[str]:
    """Uma linha pode conter vários comandos: `ruff check . && black . && isort .`."""
    linha = re.sub(r"(^|\s)#.*$", "", linha).strip()      # comentário não é comando
    return [c for c in re.split(r"&&|\|\||;", linha) if c.strip()]


def assinatura(linha: str) -> str | None:
    """`uv run pytest -v --cov=src` → 'pytest'; `cargo test --all` → 'cargo test'."""
    linha = re.sub(r"(^|\s)#.*$", "", linha).strip()
    if not linha or linha.startswith("#"):
        return None
    partes = [p for p in re.split(r"\s+", linha) if p]
    # descasca prefixos que não identificam o gate
    while partes and (partes[0] in {"uv", "uvx", "npm", "npx", "bunx", "pipx", "poetry", "pdm", "sudo", "time"}
                      or partes[0].endswith("/bin/python") or partes[0] in {"python", "python3"}):
        if partes[0] in {"uv", "poetry", "pdm", "pipx"} and len(partes) > 1 and partes[1] in {"run", "sync"}:
            partes = partes[2:]
        elif partes[0] in {"uvx", "bunx"}:
            partes = partes[1:]
            break
        elif partes[0] in {"npm", "npx"}:
            partes = partes[1:]
            if partes and partes[0] == "run":
                partes = partes[1:]
            break
        else:
            partes = partes[1:]
    if not partes or partes[0] in IGNORAR:
        return None
    # `uvx ruff@0.15.15` → ferramenta 'ruff': a versão fixada não muda o gate.
    ferramenta = partes[0].split("@", 1)[0]
    partes = [ferramenta, *partes[1:]]
    if ferramenta in {"cargo", "git", "docker", "cmake", "ctest", "go"} and len(partes) > 1:
        return f"{ferramenta} {partes[1]}"
    if ferramenta in {"ruff", "mypy", "pytest", "black", "isort", "clippy", "rustfmt",
                      "prettier", "eslint", "vitest", "playwright", "tsc", "svelte-check"}:
        return f"{ferramenta} {partes[1]}" if ferramenta == "ruff" and len(partes) > 1 else ferramenta
    return ferramenta


def expandir_make(linhas: list[str], raiz: Path) -> set[str]:
    """Assinaturas dos comandos dentro das receitas de `make <alvo>` citadas nas linhas."""
    mk = next((raiz / n for n in ("Makefile", "makefile", "GNUmakefile") if (raiz / n).is_file()), None)
    alvos = {m.group(1) for l in linhas for cmd in comandos_da_linha(l)
             if (m := re.match(r"make\s+(?:-\w+\s+)*([\w.-]+)", cmd.strip()))}
    if not mk or not alvos:
        return set()
    texto = mk.read_text(encoding="utf-8", errors="replace")
    # Receita real costuma usar variável: `$(RUFF) check $(LINT_PATHS)`. Sem expandir,
    # a ferramenta lida seria "$(RUFF)" e todo comando apareceria como ausente.
    variaveis = {m.group(1): m.group(2).strip()
                 for m in re.finditer(r"^([A-Z_][A-Z0-9_]*)\s*[:?]?=\s*(.*)$", texto, re.M)}

    def expandir(linha: str, profundidade: int = 3) -> str:
        for _ in range(profundidade):
            nova = re.sub(r"\$[({]([A-Z_][A-Z0-9_]*)[)}]",
                          lambda m: variaveis.get(m.group(1), m.group(0)), linha)
            if nova == linha:
                break
            linha = nova
        return linha

    achadas: set[str] = set()
    for alvo in alvos:
        # receita = linhas iniciadas por TAB logo após "alvo:"
        m = re.search(rf"^{re.escape(alvo)}\s*:[^=\n]*\n((?:\t.*\n|\n)*)", texto, re.M)
        if not m:
            continue
        for linha in m.group(1).splitlines():
            linha = expandir(linha.lstrip("\t").lstrip("@-"))
            for cmd in comandos_da_linha(linha):
                if (sig := assinatura(cmd)):
                    achadas.add(sig)
    return achadas


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--agents", default="AGENTS.md")
    ap.add_argument("--workflows", default=".github/workflows")
    a = ap.parse_args()

    agents, wdir = Path(a.agents), Path(a.workflows)
    if not agents.is_file():
        print(f"sem {agents} — o contrato de comandos mora nele (skill definir-stack)", file=sys.stderr)
        return 2
    arquivos = sorted([*wdir.glob("*.yml"), *wdir.glob("*.yaml")]) if wdir.is_dir() else []
    if not arquivos:
        print(f"sem workflow em {wdir} — o projeto não tem gate que roda em servidor", file=sys.stderr)
        return 2

    ilha = ILHA.search(agents.read_text(encoding="utf-8"))
    if not ilha:
        print(f"{agents}: sem a ilha 'comandos-exatos' — nada a comparar", file=sys.stderr)
        return 2
    blocos = CODIGO.findall(ilha.group(1))
    esperados: dict[str, str] = {}
    for bloco in blocos:
        for linha in bloco.splitlines():
            for cmd in comandos_da_linha(linha):
                if (s := assinatura(cmd)):
                    esperados.setdefault(s, cmd.strip())

    texto_ci = "\n".join(f.read_text(encoding="utf-8") for f in arquivos)
    linhas_ci = re.findall(r"^\s*(?:-\s*)?(?:run|cmd):\s*[|>]?-?\s*(.*)$", texto_ci, re.M)
    for bloco in re.findall(r"run:\s*\|(.*?)(?=\n\s*[-\w]+:)", texto_ci, re.S):
        linhas_ci += bloco.splitlines()
    executados = {s for l in linhas_ci for cmd in comandos_da_linha(l) if (s := assinatura(cmd))}
    # `make lint` no CI roda ruff/black/mypy por dentro: sem olhar a receita, o verificador
    # acusa como ausente o que de fato roda. Um nível de indireção basta na prática.
    executados |= expandir_make(linhas_ci, agents.parent)

    faltando = {k: v for k, v in esperados.items() if k not in executados}
    avisos: list[str] = []
    for f in arquivos:
        t = f.read_text(encoding="utf-8")
        if "continue-on-error" in t:
            avisos.append(f"{f}: 'continue-on-error' — passo que não pode reprovar não prova nada")
        if "|| true" in t:
            avisos.append(f"{f}: '|| true' mascarando falha de comando")
        if "pull_request_target" in t:
            avisos.append(f"{f}: 'pull_request_target' — roda código do PR COM segredo disponível")
        if re.search(r"uses:\s*[\w.-]+/[\w.-]+@(main|master)\b", t):
            avisos.append(f"{f}: action fixada em @main/@master — código de terceiro mudando sob o gate")
        bloco_jobs = t.split("\njobs:", 1)[1] if "\njobs:" in t else ""
        jobs = len(re.findall(r"^\s{2}[\w-]+:\s*$", bloco_jobs, re.M))
        if jobs and t.count("timeout-minutes") < jobs:
            avisos.append(f"{f}: job sem 'timeout-minutes' ({t.count('timeout-minutes')} de ~{jobs})")

    if faltando:
        print(f"{len(faltando)} comando(s) do {agents} que o CI não roda:", file=sys.stderr)
        for s, linha in sorted(faltando.items()):
            print(f"  - {s:<18} ({linha})", file=sys.stderr)
    for w in avisos:
        print(f"  ! {w}", file=sys.stderr)
    if faltando or avisos:
        print("\n  → ou o CI passa a rodar, ou o AGENTS.md deixa de prometer. Dois contratos, não.",
              file=sys.stderr)
        return 1

    print(f"gate coerente: {len(esperados)} comando(s) do AGENTS.md presentes no CI "
          f"({len(arquivos)} workflow(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())
