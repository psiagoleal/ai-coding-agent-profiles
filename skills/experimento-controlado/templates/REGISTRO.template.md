<!-- Caminho relativo: <diretório do experimento>/README.md -->

# EXP-NNNN — <a hipótese em uma linha>

- **Estado:** pré-registrado | rodado | concluído
- **Ticket:** <link>
- **Manifesto:** `experimento.json` — o commit dele **e de todas as entradas** é o pré-registro

## Hipótese

<o que se espera que a instrução mude, em que modelo, em que casos>

## Critério

<escrito antes de rodar, com as TRÊS saídas — confirmada, inconclusiva, refutada; copiado do
manifesto, nunca editado depois>

## Braços

| Braço | Arquivo | Tamanho |
|---|---|---|
| base | — | — |
| placebo | `bracos/placebo.md` | <bytes> |
| controle | `bracos/controle.md` | <bytes> — escolhido no piloto: <casos do piloto, resultado contra a base> |
| minimo | `bracos/minimo.md` | <bytes> |
| tratamento | `bracos/tratamento.md` | <bytes> |

## Casos

| Caso | Tipo | Origem | De onde veio | Correção |
|---|---|---|---|---|
| <id> | falha | desenho / novo | <a falha observada, com data> | regex / rubrica |
| <id>-gemeo | gêmeo | desenho / novo | <a mesma situação, com a evidência que decide> | regex / rubrica |

## Juiz

<modelo; concordância e kappa no `--calibrar-juiz`, com quantas respostas e quem corrigiu>

## Resultado

<preenchido depois: a saída do executor, colada, com `pré-registrado:` e o caminho do
registro; leitura por caso e por par; veredito pela LETRA do critério — confirmada,
inconclusiva ou refutada. Defeito de desenho achado depois fica ao lado do veredito, em
seção própria, e não o reescreve>

## Não medido

<outro modelo, ferramentas, várias voltas, casos fora do manifesto — o que este resultado não
autoriza afirmar>
