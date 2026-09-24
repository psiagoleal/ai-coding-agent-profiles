<!-- Caminho relativo: skills/stack/craft-de-interface/references/estruturar.md -->

# Estruturar — os elementos certos, na ordem certa

Ler quando a tela tem o conteúdo, mas o olho não sabe para onde ir.

## Diagnostique antes de mover caixa

Escreva a tese espacial: qual é o caminho de leitura, o que é grupo, onde a densidade sobe.
Mover elementos sem isso é tentativa e erro cara.

## Um objetivo primário por tela

Todo elemento justifica a existência contra esse objetivo. O que não justifica desce um nível
— ou some. Complexidade secundária vai atrás de um ponto de entrada claro, em vez de ficar
exposta "porque alguém pode precisar".

## Agrupe por proximidade, não por moldura

Espaço agrupa melhor que caixa. Só acrescente contêiner quando a proximidade já não separa.

**Nunca aninhe contêineres do mesmo tipo** — cartão dentro de cartão é sintoma de hierarquia
mal resolvida, não de organização.

## Ritmo é contraste de espaçamento

Um único valor de espaçamento repetido produz uma lista monótona. Alterne intervalos curtos
(dentro do grupo) e generosos (entre grupos). Regra simples e que quase sempre acerta:
**mais espaço acima de um título do que abaixo dele** — o título pertence ao que vem depois.

Use a escala documentada no `DESIGN.md`. Escala com passo de 4 dá degraus intermediários que
uma de 8 não tem.

## Adaptar não é escalar

Ponto de quebra fica **onde o conteúdo quebra**, não em larguras de aparelhos da moda. Largura
extra serve para **reorganizar** (duas colunas, mestre-detalhe), nunca para esticar o layout
estreito.

A arquitetura de informação é a mesma em todos os contextos: se uma função importa, ela
funciona no alvo — esconder no pequeno é decidir que não importava.

## Toque e teclado mudam a estrutura

Alvo de toque tem tamanho mínimo e respiro entre vizinhos. Nada que dependa de passar o mouse
para existir pode ser a única via de uma função.
