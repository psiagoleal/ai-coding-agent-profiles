<!-- Caminho relativo: docs/adr/0017-cadeia-spec-driven.md -->

# ADR 0017: Cadeia spec-driven, com a spec como artefato numerado

- **Status:** Accepted
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** fluxo, spec, tickets, rastreabilidade

## Contexto

Temos as peças e não temos a cadeia. Existem skill de spec-como-contrato, micro-ticket com
painel, laço de correção, gates de conclusão e ADRs numeradas — todas isoladas, sem nada que
as ligue. Na prática, trabalho nasce direto em ticket, e o ticket não sabe explicar de que
decisão ele veio.

O efeito disso já foi medido no próprio framework: quatro mudanças entraram no mesmo *merge*,
em um só dia, e a causalidade entre elas deixou de ser recuperável. Sem artefato que registre
"isto foi decidido, por isto, e gerou estes itens", a reconstrução depende de memória.

A biblioteca analisada encadeia entrevista → spec → tickets → implementação, e cada etapa
exige o artefato da anterior.

## Decisão

> A spec é artefato de primeira classe, numerada, em **`docs/specs/NNNN-<slug>.md`**. Tickets
> gerados citam a spec; a spec lista os seus tickets. A rastreabilidade vale nos dois sentidos.

### 1. A cadeia

| Etapa | Entrada | Artefato |
|---|---|---|
| entrevista | conversa | decisões resolvidas; ADR e glossário escritos **durante** |
| spec | entrevista + ADRs | `docs/specs/NNNN-*.md` |
| tickets | spec aceita | linhas no painel, citando a spec, com bloqueio nomeado |
| implementação | spec + tickets | código, com revisão **contra a spec** |

### 2. Seções fixas da spec

Problema · Solução · Histórias · Decisões de implementação · Testes · **Fora de escopo**.

A última não é ornamento: é o que permite a revisão dizer "isto não foi pedido" sem recorrer
à memória de quem pediu.

### 3. Por que não dentro da ADR

Os dois artefatos têm ciclos de vida opostos. **A ADR é permanente** e imutável depois de
aceita; **a spec se esgota** quando os seus tickets fecham. Misturá-los produziria ADR que
envelhece mal e spec que ninguém pode corrigir.

### 4. Por que não descartável

A spec explica por que o ticket existe. Jogá-la fora devolve o problema que a cadeia resolve.

## Consequências

**Positivas.** O ticket passa a ter proveniência de decisão. A revisão ganha eixo próprio —
conformidade com a spec, separada de conformidade com o padrão do repositório. "Fora de
escopo" vira declaração escrita, não combinado verbal.

**Negativas.** Mais um artefato numerado para manter em dia, e uma spec abandonada no meio do
caminho é dívida visível. Trabalho pequeno não deve gerar spec: a cadeia vale a partir de algo
que renda mais de um ticket, e essa fronteira é julgamento, não regra.

**Verificação.** Ticket que cite spec inexistente reprova; spec sem ticket por mais de uma
rodada aparece como pendência no painel.
