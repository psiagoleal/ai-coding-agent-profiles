<!-- Caminho relativo: docs/adr/0001-preferencia-por-ferramentas-open-source.md -->

# ADR 0001: Preferência por ferramentas open-source frente a soluções proprietárias

- **Status:** Accepted
- **Data:** 2026-05-28
- **Decisores:** Equipe técnica
- **Tags:** dependências, custo, reprodutibilidade

## Contexto

O projeto opera sob orçamento enxuto e precisa rodar de forma idêntica em hardware local
e em pipelines de CI/CD. Soluções proprietárias com custo de licenciamento por núcleo ou
por execução são inviáveis nesses ambientes e prejudicam a reprodutibilidade (uma execução
local pode não casar com a do CI por indisponibilidade de licença).

## Decisão

Fica acordada a **priorização de bibliotecas e ferramentas open-source maduras** para as
capacidades centrais do projeto. Quando uma capacidade exigir um motor especializado,
escolhe-se a alternativa **livre de licença** antes de qualquer opção proprietária; toda
exceção (uso de ferramenta paga/licenciada) exige um novo ADR com justificativa.

## Consequências

- **Impacto positivo:** custo zero de licenciamento em desenvolvimento e CI/CD.
- **Impacto positivo:** reprodutibilidade exata em qualquer máquina ou *runner*.
- **Impacto negativo:** em escala muito grande, ferramentas livres podem ter desempenho
  inferior a soluções dedicadas — aceitável dentro dos limites atuais do projeto.

## Diretriz de Conformidade de Código

- **Proibido:** introduzir dependências proprietárias/licenciadas ou invocações a serviços
  pagos sem um ADR que as autorize.
- **Obrigatório:** registrar e justificar qualquer exceção em um novo ADR antes de adotá-la.

> Qualquer tentativa de desvio viola as diretrizes de conformidade arquitetural e deve ser
> reportada ao operador humano antes de prosseguir.
