<!-- Caminho relativo: docs/specs/0004-linha-de-base-e-gates.md -->

# Spec 0004 — Linha de base de sessão e gates de conclusão executáveis

- **Status:** Rascunho — **uma decisão pendente** (ver fim); criticada em contexto limpo em
  2026-10-29, achados incorporados
- **Data:** 2026-10-29
- **Decide a partir de:** painel de tickets, caminho crítico "instrumentar antes de mudar
  comportamento"; skills `gates-de-conclusao` e `licoes-aprendidas`
- **Tickets:** [MT-22](../tickets/MT-22.md) → [MT-23](../tickets/MT-23.md) ·
  [MT-25](../tickets/MT-25.md) → [MT-26](../tickets/MT-26.md)

## Problema

Nenhuma afirmação do tipo "esta mudança melhorou a execução" é refutável neste framework,
porque não existe linha de base. Em 2026-10-01, regra, skills, subagentes e reorganização de
diretórios entraram no mesmo dia e no mesmo merge. Tratamentos assim ficam perfeitamente
confundidos: nenhuma medição posterior separa a causa.

A skill que governa a conclusão do trabalho, `gates-de-conclusao`, tem 217 linhas e nenhum
script. Ela está no degrau mais fraco da escada que a `licoes-aprendidas` define. E a
expectativa de um gate é código sem teste: em 29 registros reais havia 13 formas do mesmo
padrão, e a que parecia correta **aprovava** "1 failed, 11 passed" (observado em 2026-10-04).

## Solução

Duas trilhas que se encontram:

1. **Medir o passado.** Um colhedor passivo lê as transcrições de sessão que já existem e
   emite eventos carimbados com a versão do framework. Um relatório compara antes e depois de
   um commit, declarando as confusões.
2. **Tornar a conclusão verificável.** Um executor roda os gates de `GATES.md` e grava
   evidência; um lint reprova expectativa que aprova o que não devia.

O evento de gate do executor é um dos cinco sinais do colhedor. As duas trilhas medem a mesma
coisa: se "pronto" foi verdade.

## Histórias

1. **Como mantenedor**, quero perguntar "isto melhorou?" e receber número com as confusões
   declaradas, não impressão.
2. **Como mantenedor**, quero que o relatório se recuse a atribuir causa quando os
   tratamentos entraram juntos.
3. **Como agente**, quero um executor que diga se o gate passou, para não marcar checkbox sem
   evidência.
4. **Como autor de gate**, quero que o lint reprove a minha expectativa quando ela aprova
   falha.

## Decisões de implementação

| Decisão | Escolha | Onde |
|---|---|---|
| Formato do evento | JSONL append-only, todo evento com `sha` do framework e versão do esquema | MT-22 |
| Os cinco sinais | envelope da sessão; ledger de comandos (comando, código, duração, hash); evento de gate com a saída; mensagem humana de correção; desfecho em git (commit, arquivos, retrabalho) | MT-22 |
| Corte antes/depois | por timestamp de **evento**, não de sessão; o `sha` vira instante pela data de commit dele | MT-22 (erro corrigido em 2026-10-07) |
| Tratamento | commit que altera o que o agente carrega: `AGENTS.md`, `skills/`, `agents/`, configuração de harness | MT-23 |
| Definição operacional das métricas | escrita e commitada **antes** da primeira execução do relatório — o commit é o pré-registro, como na skill `experimento-controlado` | MT-23 |
| Coleta | 100% passiva, sobre arquivo existente; nada roda no laço do agente | MT-22 |
| Métricas | quatro, congeladas antes de qualquer mudança: aprovação falsa de gate, repetição de comando, correção humana por tarefa, retrabalho | MT-23 |
| Gate | sucesso exige código de saída zero **e** casamento do `EXPECT` | MT-25 |
| Abandono | `ABANDON: <id> <motivo>`, estado terminal distinto de sucesso | MT-25 |
| Conteúdo lido | ledger herdado, título de gate e saída de comando são dado não confiável | MT-25 |

## Critérios de aceite

| # | Critério | Prova | Ticket |
|---|---|---|---|
| 1 | QUANDO o colhedor roda sobre as transcrições existentes, toda linha emitida DEVE ter `sha` do framework não nulo e versão do esquema | `colher-metricas … \| jq -e 'all(.sha != null)'` | MT-22 |
| 2 | O colhedor DEVE emitir, por sessão, a taxa de repetição de comando e a contagem de correções humanas, e as duas DEVEM bater com a contagem manual de uma sessão escolhida | conferência registrada no ticket | MT-22 |
| 3 | O colhedor DEVE contar invocação de subagente separando genérico de nomeado | campo no envelope de sessão; teste com transcrição fabricada | MT-22 |
| 4 | QUANDO `relatar-metricas --antes <sha> --depois <sha>` roda, ele DEVE imprimir as quatro métricas dos dois lados, com contagem absoluta e número de sessões | execução sobre o acervo existente | MT-23 |
| 5 | SE um dos lados tem menos de duas sessões, ENTÃO o relatório DEVE recusar comparar | teste com recorte fabricado | MT-23 |
| 6 | SE mais de um tratamento entrou entre os dois `sha`, ENTÃO o relatório DEVE imprimir, junto do número, que não atribui causa | teste com dois commits de tratamento no intervalo | MT-23 |
| 7 | QUANDO um gate falha (código diferente de zero ou `EXPECT` sem casamento), o executor DEVE sair com código diferente de zero e gravar comando, diretório, código de saída e hash da saída | caso de teste do executor | MT-25 |
| 8 | QUANDO o `GATES.md` tem `ABANDON:`, o executor DEVE sair com código próprio, e o estado final NÃO DEVE ser sucesso | caso de teste do executor | MT-25 |
| 8a | SE o `GATES.md` é malformado (gate sem `EXPECT:`, `CHECK:` vazio, id repetido), ENTÃO o executor DEVE sair com código de uso, distinto de falha de gate, nomeando a linha, e NÃO DEVE rodar nenhum gate | caso de teste do executor | MT-25 |
| 8b | A definição operacional das quatro métricas DEVE estar commitada antes da primeira execução do relatório, e o relatório DEVE imprimir o commit dela | `git log` do arquivo de definição anterior ao primeiro relatório | MT-23 |
| 9 | O lint DEVE reprovar um corpus com pelo menos um achado por regra (nove regras) e as treze formas reais coletadas, nomeando a regra violada | `lint-expect --corpus` | MT-26 |

## Fora de escopo

- **Conclusão causal.** O relatório mede; não explica.
- **Emissão nativa de evento** dentro do harness. A coleta é sobre o que já é gravado.
- **Reescrever gates de terceiros.**
- **Mudar comportamento do agente** antes de a linha de base existir. É o motivo de esta frente
  vir primeiro no painel.

## Decisões pendentes

**C. Onde o ledger mora, e de quais sessões.**
As transcrições cobrem **todos** os projetos da máquina, inclusive os confidenciais, e um
comando registrado inteiro pode conter nome de projeto, caminho ou dado. Recomendação: o
colhedor lê só as sessões deste framework por padrão (filtro por `cwd`), e o ledger e os
relatórios **nunca** vão ao repositório público. Ficam fora do git, no diretório de estado do
usuário, ou no repositório privado. Medir outros projetos é opção explícita, com saída também
fora do público. A spec não passa a Aceita sem essa decisão.
