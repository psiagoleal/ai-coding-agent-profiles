<!-- Caminho relativo: docs/specs/README.md -->

# Specs

O contrato de cada frente de trabalho com mais de um ticket: o que conta como pronto, em
critérios EARS com comando de prova, e o que está fora. Cadeia na ADR 0017; formato e
adequação retroativa na ADR 0024; método na skill
[`spec-como-contrato`](../../skills/spec-como-contrato/SKILL.md).

A ADR decide e não muda. A spec fixa o resultado e se esgota quando os tickets fecham. O
ticket fixa um ciclo de trabalho e cita a spec.

| Spec | Frente | Status | Decisões pendentes | Tickets |
|---|---|---|---|---|
| [0001](0001-invocacao-declarada.md) | Invocação declarada nas skills | Aceita | — | MT-56, MT-57, MT-55, MT-58 |
| [0002](0002-instalacao-por-agente.md) | Instalação declarada por agente | Rascunho | — | MT-52, MT-53, MT-54, MT-55 |
| [0003](0003-orcamento-de-contexto.md) | Orçamento do catálogo e do arquivo de regra | Rascunho | A, B | MT-44, MT-43, MT-29, MT-31 |
| [0004](0004-linha-de-base-e-gates.md) | Linha de base de sessão e gates executáveis | Rascunho | C | MT-22, MT-23, MT-25, MT-26 |
| [0005](0005-guardas-que-declaram.md) | Guardas que declaram o que não examinaram | Rascunho | — | MT-24, MT-40, MT-41, MT-48, MT-59 |
| [0006](0006-delegacao-externa.md) | Delegação a modelo externo | Rascunho | E | MT-33, MT-34, MT-35 |

**Rascunho** não gera implementação: falta decisão do mantenedor ou crítica em contexto limpo.
**Aceita** gera. **Esgotada** é a spec com todos os tickets fechados, que fica para explicar
por que eles existiram.

## Tickets em aberto sem spec

Trabalho de um ticket só não paga spec (ADR 0017). Os abaixo estão fora de frente, e isso é
declarado aqui para não parecer esquecimento:

MT-2, MT-3, MT-6, MT-7, MT-12, MT-15, MT-16, MT-17, MT-18, MT-20, MT-21, MT-27, MT-28,
MT-30, MT-32, MT-36, MT-37, MT-38, MT-39, MT-42, MT-45, MT-46, MT-47 e MT-49 (este, um
experimento, com registro próprio em `docs/experimentos/`).

Quando dois deles passarem a depender um do outro, viram frente, e a frente ganha spec.
