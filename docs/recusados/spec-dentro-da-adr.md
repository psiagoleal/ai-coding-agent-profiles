<!-- Caminho relativo: docs/recusados/spec-dentro-da-adr.md -->

# Spec dentro da ADR

**O que foi pedido.** Não criar `docs/specs/`: escrever Histórias, Testes e Fora de Escopo
dentro da própria ADR, mantendo uma numeração só.

**Por que está fora.** Os dois artefatos têm ciclos de vida opostos. A ADR é permanente e
imutável depois de aceita; a spec se esgota quando os seus tickets fecham. Fundidos, produzem
ADR que envelhece mal e spec que ninguém pode corrigir sem violar a imutabilidade. A economia
seria de uma numeração; o custo é a imutabilidade da ADR.

**Condição de reabertura.** Se na prática as specs passarem a não se esgotar — isto é, se
virarem documento vivo consultado depois de os tickets fecharem —, a separação perde a razão e
esta recusa cai. Medir depois de cinco specs.

**Pedidos anteriores.** 2026-10-11, na rodada de decisões da análise.

**Decidido em.** ADR 0017.
