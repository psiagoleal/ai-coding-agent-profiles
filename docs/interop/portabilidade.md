<!-- Caminho relativo: docs/interop/portabilidade.md -->

# Portabilidade do acervo entre harnesses

Decisão: ADR 0012 (skills) e ADR 0013 (subagents, taxonomia). Este documento é o **mapa de
trabalho**: o que já funciona em cada harness, o que falta e como medir.

## Estado por camada

| Camada | Fonte neutra | Portável hoje? | Pendência |
|---|---|---|---|
| Instruções | `AGENTS.md` | Sim — padrão agents.md, lido por todos | Ponteiros `CLAUDE.md`/`GEMINI.md` por harness |
| Skills | `skills/` → `.claude/skills`, `.agents/skills` | Sim, via `--agent` | — |
| Subagents | `agents/` → `.claude/agents`, `.codex/agents`, `.opencode/agents` | Claude Code, Codex e OpenCode | Gerar Gemini e Copilot |
| Hooks | por skill (`limites-de-uso`) | **Só Claude Code** | Cada harness tem seu mecanismo; sem padrão comum |
| Modelo | `model:` no frontmatter do agent | Só Claude Code/ZCode | Traduzir para nível de raciocínio |

## Precedência de diretório de skills (armadilha)

O `agentry` resolve skills por **precedência de diretório, sem soma**: `.agents/skills`
primário, `.claude/skills` como alternativa. Três consequências práticas:

- **Diretório vazio vence diretório cheio.** Um `.agents/skills/` vazio faz o `.claude/skills/`
  populado ser ignorado. O instalador remove o adaptador que ele próprio deixaria vazio e
  **avisa** quando encontra um vazio que não foi ele que criou.
- **Instalar um subconjunto em `.agents/skills` esconde o resto.** Se o projeto já tinha tudo
  em `.claude/skills` e você instala só uma categoria com `--agent agentry`, o agentry passa a
  ver só essa categoria. Ele avisa na inicialização o que ficou de fora — mas o padrão certo é
  manter os dois adaptadores com a mesma seleção.
- Apontando os dois para a mesma pasta neutra, como o instalador faz, nada muda e nada é dito.

**Fronteira acordada com o `agentry` (2026-09-18).** Ele **não** vai tratar diretório primário
vazio como ausente: a precedência é do diretório, por decisão registrada na ADR-0047 dele, e
mudar isso exigiria ADR nova lá. O que ele garante é que ninguém fica sem entender — quando
`.claude/skills` tem algo que o primário não tem, os nomes saem no aviso de inicialização.
**Vazio dos dois lados continua vazio silencioso**, e é exatamente aí que a limpeza do nosso
instalador faz o trabalho: a mitigação é nossa, por construção, não dele.

Se aparecer **uso real** de seleções diferentes entre os dois adaptadores, esse é o dado que
reabriria a alternativa que a ADR-0047 rejeitou (somar com deduplicação por `name`) — e seria
ADR nova do lado deles, não emenda. Até lá, mantenha a mesma seleção nos dois.

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

1. ~~Gerador de subagents para Codex e OpenCode~~ — **feito** (`scripts/gerar-agent-adapter.py`,
   ligado ao instalador). Verificado: TOML válido para todos os subagents, corpo idêntico ao
   canônico, `sandbox_mode`/`permission` derivados das tools. Falta exercitar ao vivo nas CLIs
   (`codex debug prompt-input`, `opencode agent list`).
2. ~~`agentry`: descobrir skills em `.agents/skills`~~ — **feito** pelo projeto (ADR-0047
   dele, commit `a2192f0`).
3. Gemini e Copilot — mesmo gerador, novo ramo em `gerar-agent-adapter.py`.
4. Revisar as menções a `CLAUDE.md` e os usos de tool de subagent nos corpos.

## Restrições de terceiros que condicionam o desenho

O `agentry` avaliou subagents nomeados (ADR-0048 dele, **Proposed** — nada adotado) e registrou
duas travas que valem para o nosso formato canônico:

- **`model:` contornaria o roteador dele**, e com ele a verificação de egresso. Só entraria
  como *preferência* traduzida para classe de tarefa — o que depende exatamente da tradução
  para **nível** de raciocínio que já adotamos no gerador (`opus`→alto, `sonnet`→médio).
- **`tools:` seria uma segunda fonte de verdade** ao lado da política de permissões dele. Lá,
  só poderia **restringir** o que a política já permite, nunca ampliar; divergência entre os
  dois seria erro ao carregar. Nosso gerador já deriva permissão a partir das tools — e essa
  derivação precisa continuar sendo um piso, não um teto. **Trava em aberto do lado deles.**

A primeira trava foi **fechada** na ADR-0048 do `agentry` (commit `b691b18`) citando a nossa
tradução para nível: deixou de ser bloqueio externo e virou decisão interna deles, de mapear
nível de raciocínio para classe de tarefa.
