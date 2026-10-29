<!-- Caminho relativo: docs/specs/0002-instalacao-por-agente.md -->

# Spec 0002 — Instalação declarada por agente, registrada no projeto

- **Status:** Rascunho — sem decisão pendente; criticada em contexto limpo em 2026-10-29,
  achados incorporados; aguarda aceite do mantenedor
- **Data:** 2026-10-29
- **Decide a partir de:** ADR 0023; ADR 0022 §1 (decisão 1, que a 0023 resolveu); ADR 0012
- **Tickets:** [MT-52](../tickets/MT-52.md) → [MT-53](../tickets/MT-53.md) →
  [MT-54](../tickets/MT-54.md); [MT-55](../tickets/MT-55.md) depois do MT-52, contrato na
  [spec 0001](0001-invocacao-declarada.md)

## Problema

A instalação não registra o que instalou, e por isso a atualização desfaz o que foi escolhido.
O `atualizar-repos.sh` deduz o perfil do `AGENTS.md` e chama `--update` sem `--agent` nem
`--skills`. O instalador volta aos padrões: projeto instalado só para Codex ganha adaptador do
Claude, e a skill escolhida além do núcleo para de ser atualizada, sem aviso. Nas instalações
existentes, a combinação de adaptadores varia de projeto para projeto, então o defeito alcança
uso real.

Dois defeitos vêm junto. Arquivos de todos os harness vão para todo projeto, qualquer que seja
o `--agent`. E a contenção (lista `deny`, guarda de git, arquivo de ignorar) só existe para
Claude Code: quem troca de agente perde a proteção sem saber.

## Solução

Um manifesto versionado, `.agent-profile/instalacao.json`, registra a instalação. `--update` e
`atualizar-repos.sh` repetem o que ele diz. Cada agente declara, em dado, o que gera em cada
camada, e o fim de toda instalação imprime o que cada agente não tem. Trocar de agente é mudar
o manifesto: o instalador acrescenta o que entra e **imprime** o plano de remoção do que sai.

## Histórias

1. **Como mantenedor**, quero que atualizar repita a instalação que fiz, para não perder
   escolhas a cada atualização.
2. **Como mantenedor**, quero que o projeto receba só os arquivos dos agentes que uso, para não
   carregar configuração de ferramenta alheia.
3. **Como mantenedor**, quero ver no fim da instalação o que cada agente **não** tem, para não
   confundir "instalado" com "protegido".
4. **Como mantenedor**, quero trocar de agente sabendo o que ganho, o que perco e o que apagar,
   sem que o instalador apague por mim.
5. **Como dono de fonte privada**, quero que o manifesto versionado nunca publique o nome das
   minhas skills.

## Decisões de implementação

Todas tomadas na ADR 0023; a spec as cita, não as rediscute.

| Decisão | Escolha | Onde |
|---|---|---|
| Formato e lugar do manifesto | JSON em `.agent-profile/instalacao.json`, versionado | ADR 0023 §1 |
| Skill de fonte extra | só a contagem no versionado; a lista em `instalacao.local.json`, ignorado | ADR 0023 §1, ADR 0015 |
| Instalação anterior ao manifesto | inferir da árvore com `"origem": "inferido"`; ambiguidade pergunta ou recusa | ADR 0023 §1 |
| O que cada agente gera | tabela em dado, não em ramos de shell | ADR 0023 §2 |
| Arquivo de agente não pedido já presente | fica, e é relatado; o instalador não apaga | ADR 0023 §4 |
| Remoção na troca | impressa com conferência de impressão digital; quem apaga é a pessoa | ADR 0023 §5 |
| Impressão digital | a que `.agent-profile/` já grava por arquivo instalado; o plano compara com o arquivo atual | ADR 0023, contexto |
| Agente que saiu | agente que tem arquivo na impressão digital e não está mais em `agentes` | esta spec |
| Ambiguidade sem manifesto | com terminal interativo, pergunta; sem terminal, recusa | esta spec |
| Contenção | no git primeiro; no harness onde houver mecanismo; lacuna declarada onde não houver | ADR 0023 §3 |

## Critérios de aceite

Prova: asserção nomeada em `scripts/testar-instalador.sh`.

| # | Critério | Prova | Ticket |
|---|---|---|---|
| 1 | QUANDO uma instalação termina, o instalador DEVE gravar `.agent-profile/instalacao.json` com perfil, agentes, modo, pasta neutra, skills com `sinal`, contagem de extras, subagents, commit do framework e origem | "manifesto gravado com os campos da ADR 0023" | MT-52 |
| 2 | QUANDO `--update` roda sem argumentos num projeto instalado com `--agent codex` e uma skill de domínio, o instalador DEVE repetir os agentes e as skills do manifesto, sem criar `.claude/` e reprocessando a skill de domínio | "update sem argumentos repete o manifesto" | MT-52 |
| 3 | O manifesto versionado NÃO DEVE conter nome nem caminho de skill vinda de **fonte extra** (as do acervo público entram com nome); a lista das extras DEVE ir para `instalacao.local.json`, que o instalador põe no `.gitignore` do alvo | "fonte extra só como contagem" | MT-52 |
| 4 | SE não há manifesto e a árvore é ambígua (só `.agents/skills/`), ENTÃO o `--update` sem `--agent` DEVE perguntar com terminal interativo, e sem terminal DEVE recusar com código diferente de zero dizendo por quê | "sem manifesto e ambíguo recusa sem terminal" | MT-52 |
| 4a | SE o manifesto existe mas é JSON inválido, tem `schemaVersion` desconhecido ou falta campo obrigatório, ENTÃO o instalador DEVE recusar nomeando o problema, e NÃO DEVE regravá-lo | "manifesto inválido recusa sem regravar" | MT-52 |
| 5 | QUANDO `atualizar-repos.sh` encontra repositório sem manifesto e sem inferência possível, ele DEVE pular o repositório e imprimir o motivo | "atualizar-repos pula com motivo" | MT-52 |
| 6 | QUANDO a instalação é para `--agent codex`, o instalador NÃO DEVE criar `.claude/`, `.agentry/`, `.cursorrules` nem `.github/copilot-instructions.md` | "instala só o agente pedido" | MT-53 |
| 7 | SE existem arquivos de agente não pedido no alvo, ENTÃO o instalador DEVE mantê-los e listá-los no relatório | "não apaga agente não pedido" | MT-53 |
| 8 | Ao fim de toda instalação e atualização, o instalador DEVE imprimir a matriz agente × camada (descoberta, subagents, invocação, contenção), com lacuna escrita onde o agente não tem mecanismo | "matriz de lacunas impressa" | MT-53 |
| 9 | QUANDO os agentes do manifesto mudam de `claude` para `codex`, o `--update` DEVE gerar as camadas do Codex, NÃO DEVE apagar arquivo do Claude, e DEVE imprimir o plano de remoção com a conferência de impressão digital de cada arquivo | "troca claude → codex" | MT-54 |
| 10 | SE um arquivo do agente que sai foi editado à mão, ENTÃO o plano de remoção DEVE marcá-lo à parte, fora da lista segura | "editado à mão marcado" | MT-54 |
| 11 | QUANDO há troca de agente, o instalador DEVE imprimir a lista do que está fora do repositório (memória e configuração de usuário do harness antigo) e a orientação de promover regra de projeto para o `AGENTS.md` | "lista do que fica fora do repositório" | MT-54 |
| 12 | Na troca, o instalador DEVE gerar as camadas do agente que entra antes de imprimir o plano, e o plano NÃO DEVE propor esvaziar diretório de adaptador ainda usado por agente que fica (armadilha de precedência de `docs/interop/portabilidade.md`) | "plano não esvazia adaptador em uso" | MT-54 |
| 13 | Os critérios 1 a 3 e 6 da spec 0001 DEVEM passar com o adaptador gerado | as asserções "invocacao humano → claude", "→ codex", "→ harness sem mecanismo" e "relatório de não traduzidas" | MT-55 |

## Fora de escopo

- **Traduzir a lista `deny` para outros harness.** A spec só obriga a declarar onde ela falta
  (ADR 0023, consequências neutras). A tradução é trabalho por harness, com verificação na
  versão instalada.
- **A guarda de git no próprio git.** É a camada 1 do MT-24, na [spec 0005](0005-guardas-que-declaram.md).
  Sem ela, a matriz mostra a perda da guarda na troca, e isso é o resultado correto.
- **Derivar quais skills entram.** É o MT-43, na [spec 0003](0003-orcamento-de-contexto.md);
  aqui o campo `sinal` só é gravado.
- **Apagar qualquer arquivo.** Em nenhum caso o instalador remove arquivo do alvo.

## Decisões pendentes

Nenhuma.
