<!-- Caminho relativo: docs/adr/0019-barra-de-admissao.md -->

# ADR 0019: Barra de admissão de duas pernas

- **Status:** Accepted
- **Data:** 2026-10-11
- **Decisores:** Iago Leal (mantenedor), com Claude Code
- **Tags:** governança, tickets, escopo

## Contexto

Temos meia barra. A regra "observado em uso real" cobre a primeira perna — a mudança vem de
falha vista, não de melhoria imaginada — mas em espírito, sem formato. E a segunda perna não
existe: **uma falha real que re-proponha um conceito já recusado passa hoje sem resistência.**

Há ainda um slot arquitetural ocioso. Temos três perfis em *overlay*, que é exatamente o lugar
onde ajuste de um perfil deveria morar, e nenhuma regra mandando o pedido para lá.

## Decisão

> Um pedido entra se passar nas **duas** pernas. Quatro mecanismos, todos adotados.

### 1. Formato de evidência

Ticket nascido de falha declara, em três linhas:

```markdown
## Evidência
rodei:     <o comando ou a ação>
obtive:    <o que aconteceu>
esperava:  <o que deveria ter acontecido>
```

É falsificável, ao contrário de "observado em uso real", que só diz que alguém viu.

### 2. Estado terminal de rejeição no painel

O painel ganha a seção **Recusados**, com marcador `[~]`, separada de **Abandonados**. Hoje os
dois casos se confundem, e recusa disfarçada de abandono é recusa que volta. A linha cita a
ADR ou o arquivo em `docs/recusados/`.

### 3. Roteamento de propriedade

Antes de aceitar, decidir de quem é:

| O pedido é… | vai para |
|---|---|
| ajuste de um perfil | *overlay* do perfil |
| ramo de um harness | adaptador |
| válido para todos | base |

### 4. Portão de componibilidade

Se o comportamento se compõe de skills existentes, **não ganha skill nova** — vira
documentação de composição. É disciplina de crescimento: catálogo inchado foi o que estourou
o orçamento de descrição.

## Consequências

**Positivas.** A barra passa a ser aplicável por quem não participou da conversa original. O
*overlay* deixa de ser slot ocioso. O crescimento do catálogo ganha portão.

**Negativas.** Atrito maior para abrir ticket, e o formato de evidência não se aplica a
trabalho que não nasce de falha — skill nova de cobertura, por exemplo. Para esses, a primeira
perna é a lacuna demonstrada, não a falha observada, e isso precisa estar escrito para a regra
não virar letra morta aplicada seletivamente.

**Neutralidade de tamanho.** Correção de uma palavra e reescrita enfrentam a mesma barra.
