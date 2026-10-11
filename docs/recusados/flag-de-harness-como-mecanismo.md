<!-- Caminho relativo: docs/recusados/flag-de-harness-como-mecanismo.md -->

# Flag de harness como mecanismo de invocação

**O que foi pedido.** Escrever `disable-model-invocation: true` direto no `SKILL.md`, como faz
a biblioteca de terceiros analisada, em vez de criar campo próprio traduzido na instalação.

**Por que está fora.** O flag é de um harness; a biblioteca atende cinco. Adotá-lo como
mecanismo acopla a governança a ele e faz três harness ignorarem o interruptor **em silêncio** —
que é exatamente o modo de falha que a decisão existe para corrigir. Recusado o flag como
mecanismo, **não** a semântica: ela é adotada em campo próprio, e o flag passa a ser saída de
tradução do instalador.

**Condição de reabertura.** Se os harness convergirem para um campo comum de invocação, do
mesmo modo como convergiram para `.agents/skills/` (ADR 0012), o campo próprio vira redundante
e esta recusa cai.

**Pedidos anteriores.** 2026-10-11, na análise da biblioteca de terceiros.

**Decidido em.** ADR 0016.
