<!-- Caminho relativo: docs/adr/0024-spec-como-contrato-no-framework.md -->

# ADR 0024: Spec como contrato no próprio framework, com adequação do que já foi decidido

- **Status:** Accepted
- **Data:** 2026-10-29
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** fluxo, spec, tickets, rastreabilidade
- **Complementa:** ADR 0017

## Contexto

A ADR 0017 criou a cadeia entrevista → spec → tickets → implementação, e a spec numerada em
`docs/specs/`. A cadeia não pegou. Medido em 2026-10-29: **23 ADRs, uma spec**, e 44 tickets em
aberto, nenhum deles citando spec. A única spec, a 0001, também não seguia o formato que o
acervo ensina: os testes estavam em prosa, sem comando de prova, e a lista de tickets apontava
para uma seção que não existe.

A causa não é técnica. Quando o framework começou, a spec não era a filosofia de trabalho: a
decisão ia direto da ADR para o ticket. Desde então, os projetos que usam o framework passaram
a trabalhar pela skill `spec-como-contrato` — critério de aceite em EARS, cada critério com
prova, o que está fora escrito. O próprio framework ficou para trás do que ele ensina.

Isso aparece no painel. Três exemplos, todos de 2026-10-29:

- A ADR 0022 deixou três decisões em aberto, e o ticket que a implementa (MT-43) escolhe uma
  delas no "Fora de escopo", sem que a escolha esteja registrada como decisão.
- A spec 0001 diz que a seleção na instalação "tem spec própria". Essa spec não existe.
- MT-45 diz "depende de nada"; o MT-55 diz que o destrava. Sem spec que diga o que precisa
  ser verdade antes, cada ticket conta a sua versão.

## Decisão

> O framework segue a skill `spec-como-contrato` no próprio desenvolvimento. Toda frente com
> mais de um ticket tem spec; todo critério de aceite está em EARS e tem comando de prova. O
> que já foi decidido é adequado agora, não quando for tocado.

### 1. O formato

Seções da ADR 0017 §2, com uma troca e um acréscimo:

| Seção | O que muda |
|---|---|
| Problema · Solução · Histórias · Decisões de implementação · Fora de escopo | como na ADR 0017 |
| **Critérios de aceite** | substitui "Testes": cada critério em EARS (`DEVE`, nunca "deveria"), com o comando que o prova e o ticket que o entrega |
| **Decisões pendentes** | o que a spec não pode decidir sozinha, com a recomendação e quem decide |

Critério sem prova não vira tarefa. Spec com decisão pendente fica em **Rascunho**: não gera
implementação até a decisão entrar, porque decisão tomada pelo agente na falta da pessoa é o
erro que a skill existe para evitar.

### 2. Ciclo de vida

**Rascunho** (escrita, com decisão pendente ou sem crítica) → **Aceita** (decisões tomadas,
criticada em contexto limpo) → **Esgotada** (todos os tickets fechados). A spec esgotada fica:
é ela que explica por que os tickets existiram.

### 3. Adequação retroativa

- As frentes em aberto com mais de um ticket ganham spec agora: instalação por agente,
  orçamento de contexto, linha de base e gates, guardas e verificadores, delegação externa. A
  spec 0001 é reescrita no formato.
- **ADR aceita não é editada.** A ligação ADR → spec mora no índice de ADRs (coluna "Spec") e
  no cabeçalho da spec ("Decide a partir de"). Corrigir texto de ADR aceita para apontar spec
  seria quebrar a imutabilidade que a ADR 0017 §3 usa para separar os dois artefatos.
- Ticket em aberto ganha a linha **Spec.** com o link. Ticket que não pertence a frente nenhuma
  continua sem spec, e isso é declarado, não omitido: trabalho de um ticket só não paga spec
  (ADR 0017, consequências).

### 4. Verificação

A ADR 0017 já pedia que ticket com spec inexistente reprovasse, e que spec sem ticket
aparecesse como pendência. Nada disso foi implementado, e é parte do motivo de a cadeia não
ter pegado. Passa a ser ticket da spec de verificadores.

## Consequências

**Positivas.** O ticket explica de onde veio. A revisão ganha contrato para conferir o
entregue. Decisão em aberto deixa de ser resolvida dentro de "Fora de escopo".

**Negativas.** Seis specs de uma vez é dívida de leitura e de manutenção. Spec em Rascunho
bloqueia implementação até a pessoa decidir, e isso pode parar frentes inteiras: é o custo
aceito de não deixar o agente decidir por ela.

**Neutras.** Não muda o painel de tickets nem a ordem de execução. A spec diz o que é pronto;
a ordem continua sendo do painel.
