<!-- Caminho relativo: docs/DESIGN.md -->

# Contrato de design

> Fonte única do visual. O código **deriva** deste documento. Mudança visual entra aqui
> primeiro (skill `contrato-de-design`).

## Atmosfera

_(uma frase: tema, densidade, tom. Ex.: "escuro por padrão, denso, sóbrio — instrumento de
trabalho, não vitrine".)_

## Cores e papéis

| Token semântico | Valor (camada primitiva) | Papel — onde usa e onde **não** usa |
|---|---|---|
| `--fundo` | `--cinza-950` | Fundo da página. Nunca em cartão. |
| `--superficie` | `--cinza-900` | Cartão, painel, cabeçalho de tabela. |
| `--texto` | `--cinza-50` | Texto primário. |
| `--texto-suave` | `--cinza-400` | Rótulo, legenda, texto secundário. |
| `--acento` | `--azul-500` | Ação primária e foco. Uma por tela. |
| `--perigo` | `--vermelho-500` | Erro e ação destrutiva. Nunca decorativo. |

Contraste alvo: **WCAG AA** (4,5:1 em texto, 3:1 em elemento gráfico). Pares conferidos:
_(liste os pares e a razão medida.)_

## Tipografia

| Uso | Família | Peso | Tamanho / entrelinha |
|---|---|---|---|
| Título | | | |
| Corpo | | | |
| Código | | | |

Escala: _(razão e passos.)_

## Espaço, raio e elevação

- Espaçamento: `4 · 8 · 12 · 16 · 24 · 32 · 48` _(ajuste)_
- Raio: campo `…` · cartão `…` · diálogo `…`
- Elevação: _(em tema escuro, prefira variação de luminância a sombra opaca.)_

## Receitas por componente

### Botão
- **Fazer:** _(altura, preenchimento, estado de foco visível, largura mínima.)_
- **Evitar:** _(dois botões primários na mesma tela; texto em caixa alta.)_
- **Estados:** repouso · foco · desabilitado · carregando · erro

_(repita para campo, cartão, tabela, diálogo — só os que existem de fato.)_

## Acessibilidade

- Foco sempre visível, nunca removido sem substituto.
- Toda ação alcançável por teclado.
- Cor nunca é o único portador de informação.

## Anti-padrões deste projeto

- Valor cru (`#hex`, `rgba()`) fora da camada primitiva.
- Token primitivo consumido direto pela interface.
- _(acrescente as armadilhas que já apareceram aqui.)_
