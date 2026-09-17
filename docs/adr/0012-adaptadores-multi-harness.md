<!-- Caminho relativo: docs/adr/0012-adaptadores-multi-harness.md -->

# ADR 0012: Adaptadores multi-harness sobre a fonte neutra

- **Status:** Accepted
- **Data:** 2026-09-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** skills, portabilidade, interoperabilidade, agentry

## Contexto

A ADR 0004 estabeleceu skills executáveis numa **fonte neutra** (`skills/`) com
**adaptador por agente**. Na prática, porém, só existia um adaptador: `.claude/skills/`.
O `setup-profile.sh` tinha `--agent claude|none` e o caminho estava fixo no código.

Dois fatos mudaram o cenário:

1. **Convergiu um caminho comum entre harnesses.** `.agents/skills/` é o caminho
   documentado pela OpenAI para skills locais do Codex, é reconhecido nativamente pelo
   Gemini CLI e pelo OpenCode, e é o alvo que um harness de terceiro analisado usa para quatro dos seus
   seis harnesses. Deixou de haver um caminho por ferramenta: há `.claude/skills/` e há
   `.agents/skills/`.
2. **O projeto irmão `agentry` é um harness.** Ele já implementa descoberta de skill com
   divulgação progressiva (ADR-0023 dele) — mas lê **apenas** de `.claude/skills/`. Hoje,
   usar skills no `agentry` obriga o projeto a ter um diretório `.claude/` mesmo sem
   Claude Code instalado.

Manter um único adaptador tinha um custo que só agora ficou visível: nossa biblioteca
neutra não era, de fato, neutra na entrega — era uma biblioteca do Claude Code com uma
pasta a mais.

## Decisão

> O `setup-profile.sh` gera adaptadores para **N harnesses** a partir da mesma fonte
> neutra, com dois diretórios de destino apenas.

### 1. Dois destinos, não N
| Harness | Diretório de descoberta |
|---|---|
| `claude` | `.claude/skills/` |
| `codex`, `gemini`, `opencode`, `agentry`, `zcode` | `.agents/skills/` |

Harnesses que compartilham destino geram o diretório **uma vez só**. Acrescentar um
harness que já leia `.agents/skills/` é acrescentar um nome à lista — não um ramo novo.

### 2. `--agent` aceita lista
`--agent claude` (padrão, compatível com o que existia), `--agent claude,codex`,
`--agent all`, `--agent none`. Nome desconhecido é erro **antes** de qualquer escrita.

### 3. O adaptador continua plano e continua ponteiro
Os harnesses descobrem skills em um nível só. O link mantém o `basename` mesmo quando o
alvo é aninhado (`dominio/mockup-lab`), e a profundidade do `../` é derivada do destino,
não fixa. `--skills-mode copy` continua valendo para checkouts no Windows.

### 4. A fonte neutra não sabe quem a lê
Nenhum `SKILL.md` menciona diretório de harness. Referência a caminho de descoberta é
responsabilidade do adaptador — regra que já valia e que agora tem consequência prática.

## Consequências

**Positivas.** A biblioteca passa a ser utilizável por seis harnesses sem duplicar
conteúdo. O `agentry` deixa de exigir `.claude/` como caminho legado. A adoção de skills
de terceiros fica viável, porque o formato `SKILL.md` é o mesmo em todos.

**Negativas.** `.agents/skills/` é convenção jovem; se um harness divergir, voltamos a
ter um destino por ferramenta — mitigado pela tabela em `adapter_dir_de()`, que é o
único ponto a mudar.

**Neutras.** Não geramos subagents. O formato canônico de agent daquele harness
(`name`/`description`/`model`/`tools` com tradução de gramática por harness) fica
**fora de escopo** desta ADR — decisão separada, porque exige política de tradução de
permissões que hoje não temos.

## Ação decorrente, fora deste repositório

Recomendação ao `agentry`: acrescentar `.agents/skills/` à descoberta de
`crates/core/src/skills.rs`, por **precedência sem merge** — mesma disciplina das
ADRs 0020 e 0023 dele. A ADR-0023 declarava descoberta em múltiplos diretórios como
"YAGNI até haver demanda real"; esta ADR é a demanda real.
