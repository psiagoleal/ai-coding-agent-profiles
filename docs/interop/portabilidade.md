<!-- Caminho relativo: docs/interop/portabilidade.md -->

# Portabilidade do acervo entre harnesses

Decisão: ADR 0012 (skills) e ADR 0013 (subagents, taxonomia). Este documento é o **mapa de
trabalho**: o que já funciona em cada harness, o que falta e como medir.

## Estado por camada

| Camada | Fonte neutra | Portável hoje? | Pendência |
|---|---|---|---|
| Instruções | `AGENTS.md` | Sim — padrão agents.md, lido por todos | Ponteiros `CLAUDE.md`/`GEMINI.md` por harness |
| Skills | `skills/` → `.claude/skills`, `.agents/skills` | Sim, via `--agent` | `agentry` ler `.agents/skills` |
| Subagents | `agents/` → `.claude/agents` | **Só Claude Code** | Gerar Codex, Gemini, OpenCode, Copilot |
| Hooks | por skill (`limites-de-uso`) | **Só Claude Code** | Cada harness tem seu mecanismo; sem padrão comum |
| Modelo | `model:` no frontmatter do agent | Só Claude Code/ZCode | Traduzir para nível de raciocínio |

## Tradução de tools dos subagents

Os 44 subagents usam só estas seis:

| Claude Code | Codex (`sandbox_mode`) | Gemini CLI | OpenCode (`permission`) | Copilot |
|---|---|---|---|---|
| `Read` | — | `read_file` | `read` | `read` |
| `Glob` | — | `glob` | `glob` | `search` |
| `Grep` | — | `grep_search` | `grep` | `search` |
| `Bash` | — | `run_shell_command` | `bash` | `execute` |
| `Edit` / `Write` | `workspace-write` (senão `read-only`) | `replace` / `write_file` | `edit` (negar se ausente) | `edit` |

Nomes de tool do Gemini mudam entre versões — conferir a CLI instalada antes de gerar.

## Dívida nos corpos das skills e agents

Medido em 2026-09-17 sobre 193 unidades (149 skills + 44 agents), por busca textual — é
**heurística**: a contagem de slash commands (44) superestima, pois casa caminhos de API.

| Dependência de Claude Code | Unidades |
|---|---|
| Nenhuma | **94** |
| Slash command `/nome` (heurística) | 44 |
| Modelo `opus`/`sonnet`/`haiku` | 41 |
| Menção a `CLAUDE.md` | 23 |
| Criação de subagent pela tool `Agent`/`Task` | 9 |
| Nome de tool Claude em crase | 5 |
| Hook do Claude Code | 4 |
| MCP | 2 |
| `AskUserQuestion` / `TodoWrite` | 1 / 1 |

Regra para escrita nova, independente de harness: diga **o que** fazer ("peça confirmação ao
usuário", "delegue a um subagent revisor"), não **qual tool** chamar; cite `AGENTS.md`,
não `CLAUDE.md`.

## Ordem sugerida da etapa posterior

1. `agentry`: descobrir skills em `.agents/skills` (mudança no repositório dele).
2. Gerador de subagents para Codex e OpenCode — os dois com formato documentado e verificável
   por CLI (`codex debug prompt-input`, `opencode agent list`).
3. Gemini e Copilot.
4. Revisar os 23 `CLAUDE.md` e os 9 usos de tool de subagent nos corpos.
