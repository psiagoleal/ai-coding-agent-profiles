<!-- Caminho relativo: docs/tickets/MT-7.md -->

# MT-7 — Medir a nossa verificação contra o laço com score

**Contexto.** Adotamos o laço sem nota (`laco-de-correcao`) por argumento, não por medição. Existe um desenho alternativo, usado em outro acervo, com limiar numérico produzido pelo próprio verificador. Nenhum dos dois foi medido.

**Escopo**

- Gabarito com artefatos de defeito conhecido, por tipo (lógica local, semântica de shell, ordem entre seções).
- Rodar os dois protocolos no mesmo gabarito.
- Medir taxa de detecção, falso positivo e custo por revisão.

**Critério de aceite.** Tabela com os três números para os dois protocolos, e a decisão registrada em ADR.

**Fora de escopo.** O que não estiver acima. Mudança de escopo vira ticket novo, não
crescimento deste.
