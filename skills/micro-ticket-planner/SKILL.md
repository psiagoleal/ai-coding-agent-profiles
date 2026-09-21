---
name: micro-ticket-planner
description: >-
  Quebra histórias de usuário e demandas amplas em micro-tickets autocontidos
  que cabem em um único ciclo limpo de contexto do agente, evitando "ansiedade
  de contexto" e estouro de tokens. Aciona ao planejar sprint, refinar backlog,
  receber uma tarefa grande/ambígua, ou quando o usuário pedir para "quebrar",
  "planejar" ou "dividir" um trabalho.
---

# micro-ticket-planner — Planejamento por micro-tickets

Agentes confrontados com escopo amplo demais ou dependências ambíguas tendem a
interromper a execução precocemente ou ignorar restrições de segurança à medida que se
aproximam dos limites da janela de contexto ("ansiedade de contexto"). A mitigação é a
**granularidade fina**: cada tarefa cabe em um ciclo limpo de interação.

## Como quebrar (heurística)

1. **Uma saída verificável por ticket.** Se o ticket produz mais de um artefato testável
   independentemente, divida-o.
2. **Escopo de arquivos fechado.** Liste, no ticket, os arquivos que serão tocados. Se a
   lista é incerta ou cresce sem limite, o escopo ainda está amplo demais.
3. **Sem dependências ambíguas.** Se concluir o ticket exige uma decisão arquitetural
   ainda não tomada, primeiro registre um ADR (ver skill `adr-writer`).
4. **Cabe em um turno.** Estime se o agente consegue ler o contexto necessário, alterar e
   validar dentro de uma sessão sem podar histórico. Se não, divida.

## Formato de um micro-ticket

```markdown
### MT-<n>: <título imperativo curto>
- **Objetivo:** <resultado único e verificável>
- **Arquivos no escopo:** path/a.py, path/b.py
- **Critério de aceite:** <comando de teste/linter que deve passar>
- **Fora de escopo:** <o que explicitamente NÃO fazer aqui>
- **Depende de:** MT-<m> | ADR-<NNNN> | nenhum
```

## Painel de tickets — `docs/TICKETS.md`

Todo ticket gerado entra num checklist único, para quem acompanha ver **de relance** o que foi
feito e o que falta. É um índice, não um segundo lugar para o detalhe:

```markdown
## Em aberto
- [ ] [MT-12](plano.md#mt-12) — Rejeitar reserva sobreposta com 409

## Concluídos
- [x] [MT-11](plano.md#mt-11) — Validar tamanho do corpo da requisição

## Abandonados
- [~] [MT-9](plano.md#mt-9) — Cache de sessão · motivo: substituído pelo MT-11
```

Regras, todas obrigatórias:

- **Uma linha por ticket:** identificador com **link para o detalhe** e uma frase curta. Nada
  de critério de aceite, arquivos ou discussão aqui — isso mora no destino do link.
- **O link aponta para onde o ticket está detalhado:** âncora no plano (`plano.md#mt-12`) ou
  arquivo próprio (`tickets/MT-12.md`). Link quebrado é painel mentindo.
- **Atualize sempre, no mesmo trabalho:** ao **criar** (entra em aberto), ao **concluir**
  (marca `[x]` e move), ao **abandonar** (marca `[~]` com o motivo em uma frase). Nunca apague
  um ticket: o abandonado também é história.
- **Sem duplicar o handoff.** `docs/CURRENT-STATE.md` diz o que está acontecendo agora; o
  painel diz o que existe. O handoff aponta para o painel, não o copia.

O modelo está em `templates/TICKETS.template.md`; o instalador já entrega `docs/TICKETS.md` em
todo projeto novo, e nunca o sobrescreve.

## Conexão com os rituais ágeis (DoD)

Um micro-ticket só é "Concluído" quando:
- os scripts de teste/linter definidos no `AGENTS.md` passam;
- o `docs/CURRENT-STATE.md` foi atualizado (ver skill `handoff-updater`);
- o `docs/TICKETS.md` marca o ticket como concluído;
- a revisão humana de PR foi feita (ver skill `pr-review-guard`).

## Definição de pronto da skill

- [ ] Cada micro-ticket tem objetivo único, escopo de arquivos fechado e critério de aceite.
- [ ] Dependências e itens fora de escopo estão explícitos.
- [ ] Nenhum ticket exige decisão arquitetural não registrada em ADR.
- [ ] Todo ticket criado, concluído ou abandonado está refletido em `docs/TICKETS.md`, com
      link válido para o detalhe e uma frase curta.
