# Boas práticas de apresentação técnica

Síntese de pesquisa (nov/2026) aplicada ao template da skill. Onde não há fonte
primária, o item vem marcado **prática corrente**: vale como regra de trabalho,
não como evidência.

## 1. Narrativa antes do design

| Regra | Como aplicar no deck | Fonte |
|---|---|---|
| Resposta primeiro | O slide 1 ou 2 diz a recomendação. Argumentos depois, dados no fim ou no apêndice | Minto, *Pyramid Principle* ([resumo](https://slideworks.io/resources/the-pyramid-principle-mckinsey-toolbox-with-examples)) |
| Ideia central em uma frase | Escrever a frase antes do primeiro slide. Ela tem ponto de vista e o que está em jogo | Duarte ([Big Idea](https://www.duarte.com/resources/secret-structure-great-talks/)) |
| Situação → complicação → questão → resposta (SCQA) | Abertura curta: contexto conhecido, o que mudou, a pergunta, a resposta | Derivado de Minto; **prática corrente** |
| Título-afirmação | Título é uma frase completa com a conclusão do slide, até 2 linhas. O corpo é a evidência visual | Alley, *assertion-evidence* ([Penn State](https://writing.engr.psu.edu/eye_presenting.pdf), [site](https://www.assertion-evidence.com/)). Há crítica à base empírica (Farkas) |
| Storyboard de títulos | Lista dos títulos-afirmação aprovada antes de desenhar. Lida em sequência, conta a história sozinha | **prática corrente** |
| Fechar com a decisão pedida | Último slide pede uma ação com data. Não terminar em "dúvidas?" | Duarte (chamada à ação) |
| Apêndice | Detalhe que só responde pergunta vai depois do fechamento | **prática corrente** |

Público executivo: resposta, impacto, decisão, em poucos slides. Público técnico:
o mesmo esqueleto, com mais evidência e método. Ver ordem de Minto acima.

## 2. Design do slide

Princípios de Mayer (aprendizagem multimídia), com efeitos de meta-análise
citados em resumos secundários ([OSU](https://u.osu.edu/multimedialearning/?p=11),
[JSU](https://iep.jsu.edu/online/faculty/MultimediaPrinciples_Summary.pdf)):

| Princípio | Regra no slide |
|---|---|
| Coerência | Tirar tudo que não sustenta o título: enfeite, ícone decorativo, texto de apoio longo |
| Sinalização | Guiar o olho: cor de ênfase, callout, revelação em passos (`.passo`) |
| Redundância | Não projetar o texto que vai ser falado. O que se fala vai em `.notas` |
| Contiguidade espacial | Rótulo junto do elemento: rotular a série no gráfico, não em legenda distante |
| Segmentação | Uma ideia por slide; sequência longa vira passos |

- **Uma mensagem por slide, pouco texto** ([Reynolds](https://garrreynolds.com/design-tips)).
- **Contraste**: texto ≥ 4,5:1, texto grande ≥ 3:1 (WCAG 2.1, 1.4.3 —
  [W3C](https://w3c.github.io/wcag/understanding/contrast-minimum.html)). Projetor
  lava as cores: trate o mínimo como piso. `tema.py verificar` cobra 4,5:1 em todo
  par de texto.
- **Tamanho de fonte**: não há norma; a regra "30 pt" é heurística
  ([Kawasaki](https://guykawasaki.com/the_102030_rule/)). No canvas 1600×900 do
  template: corpo 30 px, título 50 px, nada abaixo de 18 px (rodapé). Teste na sala.
- **Daltonismo**: nunca codificar só por cor; somar rótulo, forma ou posição.
  Teste: a figura em tons de cinza continua legível
  ([Datawrapper](https://www.datawrapper.de/blog/colorblindness-part2)).
- **Grade e alinhamento**: as margens do template (96 px laterais) são a grade.
  Figura e texto alinham nela. **prática corrente**

## 3. Dados e gráficos

- **Cinza + uma cor de ênfase**: contexto em `--cinza`, a mensagem em `--enfase`
  (Knaflic, *Storytelling with Data* — [O'Reilly](https://www.oreilly.com/library/view/storytelling-with-data/9781119002253)).
- **Tinta de dados (Tufte)**: remover moldura, grade pesada, 3D, sombra. Sem exagerar:
  eixo e unidade ficam ([NN/g](https://www.nngroup.com/articles/clutter-charts/)).
- **Escolher o gráfico pela pergunta** (**prática corrente**): comparar categorias → barras
  horizontais ordenadas; evolução → linha; parte do todo → barra empilhada 100%
  (evitar pizza com mais de 3 fatias); distribuição → histograma/boxplot;
  relação → dispersão.
- **Rótulo direto** em vez de legenda; **unidade** no eixo ou no rótulo; **fonte**
  no rodapé do slide (`.fonte`). **prática corrente**
- **Título do gráfico = título do slide.** Não repetir título dentro da figura.
- **Tabela**: números à direita (`td.num`), mesma casa decimal, linha da recomendação
  com `tr.destaque`, no máximo ~7 linhas visíveis.

## 4. Diagramas, equações e capturas (**prática corrente**)

- **Diagrama**: só os blocos que a mensagem precisa; fluxo da esquerda para a
  direita ou de cima para baixo; um losango de decisão vale mais que dez caixas.
- **Unifilar e circuito**: mostrar só o trecho em discussão; rotular tensão,
  potência e identificação do equipamento (52-1, T1).
- **Equação**: uma por vez (`.passo`), sempre com a lista de símbolos e unidades
  (`dl.simbolos`). Dizer em palavras o que a equação afirma.
- **Captura de tela**: recortar no elemento (`--seletor`), nunca a tela inteira
  com barra de navegador; destacar o ponto (`--destacar`); ocultar dado sensível
  (`--ocultar`).
- **GIF/vídeo**: só quando o movimento é a mensagem (um fluxo de tela, uma
  animação de fenômeno). Curto (≤ 10 s), em loop, sem som.

## 5. Entrega

- **Ensaiar com cronômetro** (painel `N` mostra o tempo). A regra de 1–2 min por
  slide não tem fonte; meça no ensaio. **prática corrente**
- **Notas do apresentador** em `<aside class="notas">`: o que dizer, não o que está escrito.
- **Duas versões**: projeção (pouco texto, revelação em passos) e leitura (`L` ou
  `?modo=leitura` mostra as notas; tema `impressao` para PDF).
- **PDF**: `captura.mjs deck … --pdf` gera uma página por slide, com todos os passos visíveis.
- **Offline**: o arquivo final abre sem rede (`construir.mjs --estrito` falha se houver recurso externo).

## 6. Checklist de revisão do deck

1. A ideia central está no slide 1 ou 2, em uma frase.
2. Os títulos, lidos em sequência, contam a história sozinhos.
3. Todo título é frase-conclusão, não rótulo de tópico.
4. Uma ideia por slide; nada sobra que não sustente o título.
5. O que é falado está nas notas, não projetado.
6. Rótulo junto do elemento; legenda só se inevitável.
7. Ênfase por uma cor + cinza, nunca só cor (teste em cinza).
8. `tema.py verificar` passa (contraste AA em todos os temas usados).
9. Gráfico escolhido pela pergunta, com unidade e fonte; sem título duplicado.
10. Equação com símbolos explicados; uma por vez.
11. GIF/vídeo só onde o movimento é a mensagem; ≤ 10 s; ≤ 5 MB.
12. Nenhum texto abaixo de 18 px no canvas; nada cortado (revisar os PNG exportados).
13. Último slide pede uma decisão ou ação com data.
14. Ensaio cronometrado feito.
15. Arquivo final construído com `--estrito` e PDF exportado; sem dado de cliente fora do perímetro.
