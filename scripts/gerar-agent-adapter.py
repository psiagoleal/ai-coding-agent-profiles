#!/usr/bin/env python3
# Caminho relativo: scripts/gerar-agent-adapter.py
"""Gera o adaptador de um subagent para outro harness, a partir do formato canônico.

Canônico = frontmatter do Claude Code (`name`, `description`, `model`, `tools`) + corpo
Markdown (ADR 0013). O corpo é o mesmo em todos os harnesses; só o cabeçalho muda.

    scripts/gerar-agent-adapter.py <harness> <agent.md> <dir-destino>

Harnesses: codex (.toml), opencode (.md). Imprime o caminho gerado.

Tradução de `tools` (o corpo continua citando os nomes do Claude Code):

    Claude      Codex                     OpenCode (permission)
    Read/Glob/Grep   —                    read/glob/grep  (sempre permitidos)
    Bash        —                          bash: allow
    Edit/Write  sandbox_mode=workspace-write   edit: allow
    (sem Edit/Write)  sandbox_mode=read-only   edit: deny

`model` só tem efeito em Claude Code/ZCode. Aqui vira NÍVEL de raciocínio, nunca nome de
modelo: opus→high, sonnet→medium, haiku→low; `inherit` (ou ausente) não emite nada.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

MARCA = "gerado por scripts/gerar-agent-adapter.py — edite o canônico em agents/ e rode de novo"
ESFORCO = {"opus": "high", "sonnet": "medium", "haiku": "low"}


def ler(agente: Path) -> dict:
    texto = agente.read_text(encoding="utf-8")
    m = re.match(r"^---\n(.*?)\n---\n(.*)$", texto, re.S)
    if not m:
        sys.exit(f"{agente}: sem frontmatter YAML")
    fm, corpo = m.group(1), m.group(2).strip()

    def campo(chave: str) -> str:
        c = re.search(rf"^{chave}:\s*(.*)$", fm, re.M)
        return c.group(1).strip().strip('"').strip("'") if c else ""

    tools = [t.strip() for t in campo("tools").split(",") if t.strip()]
    nome = campo("name") or agente.stem
    if nome != agente.stem:
        sys.exit(f"{agente}: name '{nome}' difere do nome do arquivo")
    return {"nome": nome, "descricao": campo("description"), "model": campo("model"),
            "tools": tools, "corpo": corpo, "escreve": bool({"Edit", "Write"} & set(tools))}


def toml_basico(valor: str) -> str:
    return '"' + valor.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ") + '"'


def toml_multilinha(valor: str) -> str:
    # string multilinha TOML: escapa a barra e qualquer ocorrência das três aspas
    return '"""\n' + valor.replace("\\", "\\\\").replace('"""', '\\"\\"\\"') + '\n"""'


def gerar_codex(a: dict, destino: Path) -> Path:
    linhas = [f"# {MARCA}",
              f"name = {toml_basico(a['nome'])}",
              f"description = {toml_basico(a['descricao'])}",
              f'sandbox_mode = "{"workspace-write" if a["escreve"] else "read-only"}"']
    if a["model"] in ESFORCO:
        linhas.append(f'model_reasoning_effort = "{ESFORCO[a["model"]]}"')
    linhas.append("developer_instructions = " + toml_multilinha(a["corpo"]))
    alvo = destino / f"{a['nome']}.toml"
    alvo.write_text("\n".join(linhas) + "\n", encoding="utf-8")
    return alvo


def gerar_opencode(a: dict, destino: Path) -> Path:
    desc = a["descricao"].replace('"', "'")
    fm = ["---", f'description: "{desc}"', "mode: subagent", "permission:",
          f'  edit: {"allow" if a["escreve"] else "deny"}',
          f'  bash: {"allow" if "Bash" in a["tools"] else "deny"}',
          f'  webfetch: {"allow" if {"WebFetch", "WebSearch"} & set(a["tools"]) else "deny"}',
          "---", ""]
    alvo = destino / f"{a['nome']}.md"
    alvo.write_text("\n".join(fm) + f"<!-- {MARCA} -->\n\n{a['corpo']}\n", encoding="utf-8")
    return alvo


def main() -> int:
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    harness, agente, destino = sys.argv[1], Path(sys.argv[2]), Path(sys.argv[3])
    if not agente.is_file():
        sys.exit(f"agent inexistente: {agente}")
    destino.mkdir(parents=True, exist_ok=True)
    a = ler(agente)
    alvo = {"codex": gerar_codex, "opencode": gerar_opencode}.get(harness)
    if not alvo:
        sys.exit(f"harness sem gerador: '{harness}' (há: codex, opencode)")
    print(alvo(a, destino))
    return 0


if __name__ == "__main__":
    sys.exit(main())
