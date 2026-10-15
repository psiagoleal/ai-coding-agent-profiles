<!-- Caminho relativo: <diretório do experimento>/README.md -->

# EXP-NNNN — <a hipótese em uma linha>

- **Estado:** pré-registrado | rodado | concluído
- **Ticket:** <link>
- **Manifesto:** `experimento.json` — o commit dele é o pré-registro

## Hipótese

<o que se espera que a instrução mude, em que modelo, em que casos>

## Critério de refutação

<escrito antes de rodar; copiado do manifesto, nunca editado depois>

## Braços

| Braço | Arquivo | Tamanho |
|---|---|---|
| base | — | — |
| controle | `bracos/controle.md` | <bytes> |
| tratamento | `bracos/tratamento.md` | <bytes> |

## Casos

| Caso | Tipo | De onde veio | Correção |
|---|---|---|---|
| <id> | falha | <a falha observada, com data> | regex / rubrica |
| <id> | não-regressão | <o que a instrução não deveria piorar> | regex / rubrica |

## Resultado

<preenchido depois: a tabela do executor, colada, com `pré-registrado:` e o caminho do
registro; leitura por caso; veredito — adotado, inconclusivo ou recusado>

## Não medido

<outro modelo, ferramentas, várias voltas, casos fora do manifesto — o que este resultado não
autoriza afirmar>
