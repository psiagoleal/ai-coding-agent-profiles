<!-- Caminho relativo: docs/adr/0013-taxonomia-subagents-e-bibliotecas-multiplas.md -->

# ADR 0013: Taxonomia por categoria, subagents na fonte neutra e bibliotecas múltiplas

- **Status:** Accepted
- **Data:** 2026-09-17
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, subagents, taxonomia, portabilidade, interoperabilidade

## Contexto

A biblioteca cresceu além do que a organização em dois níveis (governança na raiz +
`dominio/`) sustenta: acervos com centenas de skills e dezenas de subagents passaram a ser
incorporados. Quatro fatos pesaram:

1. **Custo fixo de contexto.** Cada skill instalada deixa a sua *description* sempre no
   contexto. Um acervo de ~150 skills soma ~16 mil tokens fixos — mais caro que o trabalho que
   ele orienta, se tudo for instalado por padrão.
2. **Skills dependem de subagents.** A ADR 0012 deixou a distribuição de subagents fora de
   escopo; skills que os citam ficavam com referências penduradas.
3. **Nem todo material é publicável.** Parte do acervo tem procedência de terceiros não
   resolvida ou é de uso pessoal do mantenedor, e este repositório é público.
4. **Uso geral.** O acervo precisa servir aos principais harnesses, não só ao Claude Code.

## Decisão

### 1. Taxonomia: categoria é diretório, nome é único
- Governança na raiz de `skills/`: o **único** conjunto instalado por padrão.
- Todo o resto em `skills/<categoria>/<nome>/`, opt-in. Categorias em PT (ex.: `planejamento`,
  `verificacao`, `design`, `ml`, `fluxos`, `dominio`).
- Nomes em PT, *kebab-case*, **sem numeração**, **únicos em todas as fontes** — os adaptadores
  são planos (ADR 0012), dois nomes iguais colidiriam.
- Verificadores começam com `verificar-`, preservando o par construtor↔verificador.
- `--skills` aceita nome sem caminho, `'categoria/*'` e `@padrao`. Seleção inválida é erro
  **antes** de qualquer escrita no alvo.

### 2. Subagents na fonte neutra, formato canônico do Claude Code
- `agents/<nome>.md`, frontmatter `name`, `description`, `model`, `tools`.
- `--agents auto` (padrão): só os subagents citados pelas skills selecionadas.
- Adaptadores: Claude Code por symlink (o formato canônico é o dele); Codex e OpenCode
  **gerados** por `scripts/gerar-agent-adapter.py` (cabeçalho traduzido, corpo idêntico);
  Gemini e Copilot recebem os arquivos na pasta neutra e um aviso de pendência (seção 4).

### 3. Bibliotecas múltiplas
- O instalador lê o framework **e** bibliotecas extras com a mesma estrutura (`skills/`,
  `agents/`): `--fonte <dir>` (repetível) ou `fontes_extras` no `config.toml`, que é pessoal e
  não versionado — o caminho de uma biblioteca privada nunca aparece aqui.
- Nome repetido entre fontes (skill×skill, agent×agent ou skill×agent) é **erro**.
- Material não publicável mora em biblioteca extra privada. A dependência é num sentido só: a
  biblioteca privada depende deste framework, nunca o contrário.

### 4. Mapa de portabilidade (etapa posterior, já dimensionada)

| Harness | Instruções | Skills | Subagents | Estado |
|---|---|---|---|---|
| Claude Code | `CLAUDE.md` → `AGENTS.md` | `.claude/skills` | `.claude/agents` (mesmo formato) | **Pronto** |
| Codex | `AGENTS.md` | `.agents/skills` | `.codex/agents/*.toml` — `developer_instructions`, `sandbox_mode`, `model_reasoning_effort` | **Pronto** |
| Gemini CLI | `GEMINI.md` → `AGENTS.md` | `.agents/skills` | `.gemini/agents/*.md` — tools próprias | Skills prontas; agents pendentes |
| OpenCode | `AGENTS.md` | `.agents/skills` | `.opencode/agents/*.md` — `permission` | **Pronto** |
| GitHub Copilot | `AGENTS.md` + `.github/copilot-instructions.md` | `.agents/skills` | `.github/agents/*.agent.md` | Skills prontas; agents pendentes |
| agentry | `AGENTS.md` (ADR-0023 dele) | **só `.claude/skills`** hoje | despacho por `task_class`, sem subagent nomeado | Depende do `agentry` (solicitado) |

`model` só tem efeito em Claude Code/ZCode; a tradução deve mapear para **nível** de raciocínio,
não para nome. Tabela de tools e dívida medida: `docs/interop/portabilidade.md`.

## Consequências

**Positivas.** Acervos grandes sem custo fixo para quem não opta; subagents distribuídos com as
skills que os usam; material não publicável fora do repositório público sem perder a
integração; caminho para os outros harnesses dimensionado.

**Negativas.** Duas bibliotecas para manter em sincronia, com risco de vazamento do privado para
o público — mitigado por verificação no lado privado (a lista do que não pode vazar não pode
morar aqui). Instalação em máquina sem a biblioteca extra recebe só o conjunto público.

**Neutras.** Skills de domínio já existentes não foram reclassificadas nesta rodada: mover
quebraria instalações existentes.
