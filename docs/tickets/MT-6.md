<!-- Caminho relativo: docs/tickets/MT-6.md -->

# MT-6 — Propagar painel, hook e skills novas aos repositórios de ~/dev

**Contexto.** 22 repositórios têm o framework instalado numa versão anterior ao painel de tickets, ao hook `commit-msg` e às skills de stack.

**Escopo**

- Rodar `--update` com `--dry-run` antes, repositório a repositório.
- Ativar o hook `commit-msg` em cada clone.
- Repositórios públicos recebem só a biblioteca pública.

**Critério de aceite.** Todo repositório com framework tem `docs/TICKETS.md`, hook ativo, e `git diff` revisado.

**Fora de escopo.** O que não estiver acima. Mudança de escopo vira ticket novo, não
crescimento deste.
