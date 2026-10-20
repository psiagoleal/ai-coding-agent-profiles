<!-- Caminho relativo: docs/adr/0023-instalacao-por-agente-e-troca-de-agente.md -->

# ADR 0023: Instalação por agente, manifesto de instalação e troca de agente

- **Status:** Accepted
- **Data:** 2026-10-16
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** instalador, harness, portabilidade, manifesto

## Contexto

A ADR 0012 fez a biblioteca de skills chegar a seis harnesses por adaptador. A pergunta que
ela não respondeu é o que acontece com o **resto** da instalação quando o harness muda — num
projeto novo, ou num projeto em andamento que troca de agente.

Medido no `setup-profile.sh` e no `atualizar-repos.sh` em 2026-10-16, a instalação tem três
camadas, e só a primeira é neutra:

| Camada | O que é | Hoje |
|---|---|---|
| **Conteúdo** | `AGENTS.md`, `skills/`, `agents/`, `docs/`, hook `commit-msg` do git | neutra: lida por todos, ou aplicada pelo próprio git |
| **Descoberta** | onde o harness acha skills e subagents; arquivo de instrução que ele lê | por harness; `--agent` cobre skills e subagents |
| **Contenção** | lista `deny`, hooks, arquivo de ignorar | **só Claude Code** (28 `deny`, guarda de git no `PreToolUse`, `.claudeignore`), e o `agentry` em parte |

Três defeitos decorrem disso:

1. **A instalação não registra o que instalou.** `.agent-profile/` guarda só a impressão
   digital dos arquivos. O `atualizar-repos.sh` deduz o perfil do `AGENTS.md` e chama
   `--update` sem `--agent` e sem `--skills`: projeto instalado só para Codex ganha adaptador
   do Claude na primeira atualização, e as skills escolhidas além do núcleo deixam de ser
   atualizadas, sem aviso. As instalações existentes já têm combinações diferentes de
   adaptadores, então o defeito não é hipotético.
2. **Arquivos de todos os harnesses vão para todo projeto.** `.claude/settings.json`,
   `.agentry/`, `.cursorrules`, `.github/copilot-instructions.md` e `CLAUDE.md` são copiados
   qualquer que seja o `--agent`.
3. **A contenção não acompanha a troca de agente.** Quem sai do Claude Code para outro harness
   perde a guarda de git e a lista `deny` em silêncio. O conteúdo migra; a proteção não.

Há ainda duas consequências de decisões já tomadas:

- A **spec 0001** traduz `invocacao: humano` para o mecanismo de cada harness
  (`disable-model-invocation: true` no Claude Code, `allow_implicit_invocation: false` no
  Codex). Symlink para o `SKILL.md` neutro não carrega cabeçalho por harness: para essas
  skills o adaptador deixa de poder ser ponteiro.
- A **memória do harness mora fora do repositório** (no Claude Code, em
  `~/.claude/projects/…/memory`). Regra de projeto aprendida ali não atravessa a troca.

## Decisão

> A instalação passa a ser **declarada por agente** e **registrada no projeto**. Trocar de
> agente é editar o registro e atualizar; o instalador acrescenta o que o agente novo exige,
> relata o que ele não consegue ter, e imprime — sem executar — a remoção do que saiu.

### 1. Manifesto de instalação: `.agent-profile/instalacao.json`

Resolve a decisão 1 que a ADR 0022 deixou em aberto. JSON porque o instalador é bash e já
depende de `jq`. Versionado, ao lado da impressão digital que já existe.

```json
{
  "schemaVersion": 1,
  "perfil": "empresa",
  "agentes": ["claude", "codex"],
  "modo": "symlink",
  "pasta_neutra": "skills",
  "skills": [
    {"nome": "secrets-guard", "sinal": "nucleo"},
    {"nome": "dominio/mockup-lab", "sinal": "pedido"}
  ],
  "skills_extras": 12,
  "subagents": "auto",
  "framework": "7f3f150",
  "origem": "instalado"
}
```

- `sinal` é a razão de cada skill estar ali — `nucleo`, `pedido`, `detectado:<marcador>` —, o
  campo que o MT-43 preenche na derivação (ADR 0022 §2).
- **O manifesto nunca grava nome de skill de fonte extra nem caminho de fonte.** Elas moram em
  `skills/privado/`, fora do git (ADR 0015); listá-las num arquivo versionado as publicaria
  pelo manifesto. Entra só a contagem (`skills_extras`); a lista vai para
  `.agent-profile/instalacao.local.json`, ignorado pelo git.
- `--update` e `atualizar-repos.sh` **leem** o manifesto. Linha de comando que o contradiz é
  troca declarada, e o manifesto é regravado.
- Instalação anterior ao manifesto: o `--update` infere o que puder da árvore (adaptadores,
  pasta neutra) e grava com `"origem": "inferido"`. Onde a inferência for ambígua —
  `.agents/skills/` serve a cinco harnesses — **pergunta**, ou recusa sem `--agent` explícito.
  Nunca escolhe o padrão em silêncio.

### 2. Cada agente declara o que gera em cada camada

Uma tabela em dado (não em ramos de shell) diz, por agente: arquivo de instrução, destino de
skills e de subagents, tradução de `invocacao`, e mecanismo de contenção. O que um agente não
tem é **lacuna declarada**, e o fim de toda instalação imprime a matriz:

```
              descoberta  subagents  invocacao  contenção
  claude      ok          ok         ok         deny + hook + ignore
  codex       ok          ok         ok         — sem tradução do deny (lacuna)
```

Quem lê "instalado" sabe o que cada agente não tem.

### 3. Contenção no git primeiro

O que puder ser aplicado pelo git vale para qualquer agente e sobrevive a qualquer troca: o
hook `commit-msg` já é assim. A guarda de comando git ganha o mesmo destino pela camada 1 do
MT-24, que fica com um segundo motivo além das quatro lacunas que fecha. O que só existe no
harness — a lista `deny`, o arquivo de ignorar — é traduzido onde houver mecanismo e
declarado onde não houver.

### 4. Instala só o pedido

Arquivos de descoberta e contenção de um agente entram só se ele está em `agentes`. Nas
instalações existentes, arquivo de agente não pedido **fica** e é relatado; o instalador
continua sem apagar.

### 5. Troca de agente

1. `agentes` muda (no manifesto ou por `--agent` com `--update`).
2. O `--update` gera as camadas do agente que entrou.
3. Para o agente que saiu, imprime um **plano de remoção**: os arquivos, e para cada um se a
   impressão digital confere — editado à mão é marcado, não entra no plano como seguro. Quem
   apaga é a pessoa.
4. Imprime a lista de verificação do que fica fora do repositório: memória e configuração de
   usuário do harness antigo. Regra de projeto que só existia na memória do harness é
   **promovida** para o `AGENTS.md` ou para uma skill antes da troca.
5. Coexistência é caso particular: dois agentes no mesmo projeto, com a matriz do §2 mostrando
   onde a contenção é desigual.

### 6. Adaptador gerado para skill com `invocacao: humano`

Para essas skills o adaptador é um diretório real: `SKILL.md` **gerado** com o cabeçalho
traduzido para o harness e o corpo idêntico, e os demais arquivos da skill por symlink. As
outras skills continuam por symlink inteiro. É o mesmo modelo que os subagents já usam
(`gerar-agent-adapter.py`).

## Consequências

**Positivas.** Atualizar deixa de desfazer escolhas. Trocar de agente vira operação
declarada, com o custo à vista. O projeto deixa de carregar configuração de ferramenta que não
usa. A pergunta "por que esta skill está aqui?" ganha onde ser respondida.

**Negativas.** Muda o comportamento padrão: quem dependia de receber `.claude/settings.json`
sem pedir Claude passa a precisar pedi-lo. O adaptador gerado tem custo de regeneração a cada
`--update`, que o symlink não tinha. A tabela por agente é manutenção recorrente, e envelhece
quando o harness muda de versão.

**Neutras.** A decisão não traduz a lista `deny` para nenhum harness: só obriga a declarar onde
ela falta. A tradução é trabalho por harness, com verificação na versão instalada.

## Relação com outras decisões

Resolve a decisão 1 da ADR 0022 (formato e lugar do manifesto). Implementa a parte de
instalador da spec 0001. Dá à camada 1 do MT-24 um segundo motivo. Complementa a ADR 0012,
que tratou só da camada de descoberta.

**Tickets.** MT-52 (manifesto), MT-53 (instalação por agente e matriz de lacunas), MT-54
(troca de agente), MT-55 (adaptador gerado para `invocacao`).
