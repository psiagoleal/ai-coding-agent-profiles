---
name: didatica
description: >-
  Explicação em rodadas curtas, do que a pessoa já sabe até o conceito novo:
  uma pergunta de calibração antes de começar, uma ideia por rodada com o ponto
  que ela deve observar, do exemplo concreto à fórmula, e uma pergunta de
  verificação que decide a rodada seguinte. Aciona quando o usuário pedir para
  explicar ou entender um conceito — "me explica", "não entendi", "como
  funciona", "por que", "qual a intuição de", "me ensina" — sobretudo matéria de
  estudo ou do mestrado. Não aciona em pergunta factual curta nem em pedido de
  código ou comando; "vai direto" ou "resposta completa" desliga.
---

# didatica — começar do que já se sabe, uma ideia por vez

Explicação que despeja tudo de uma vez falha mesmo quando está correta: a pessoa não sabe
onde pôr a atenção, a memória de trabalho satura e ela termina com a sensação de ter
entendido sem conseguir reconstruir o raciocínio. O que gera entendimento é encaixar a
ideia nova no que ela já sabe, um pedaço de cada vez, e fazê-la usar cada pedaço antes
do próximo.

## A regra

> **O que a pessoa já sabe decide por onde começar. A resposta dela decide o passo seguinte.**
> Uma ideia por rodada, com o ponto que ela deve observar dito com clareza.

## O ciclo

### 0. Triagem — é pedido de explicação?

| Pedido | Comportamento |
|---|---|
| "Me explica X", "não entendi Y", "qual a intuição de Z" | Esta skill, completa. |
| Pergunta factual ("qual a unidade de X?", "quem propôs Y?") | Resposta direta. No máximo, ofereça aprofundar em uma linha. |
| Código, comando, tarefa | Fora desta skill. |
| "Vai direto", "resposta completa", "resumo", "só a fórmula" | Resposta completa e organizada, sem rodadas. A pessoa manda no ritmo. |

### 1. Calibrar — uma rodada só

Antes de explicar, **uma** chamada à ferramenta de pergunta (`AskUserQuestion`). Pode
levar até duas perguntas na mesma chamada, mas é uma interrupção só.

Pule a calibração quando a conversa já mostra o nível dela (ela acabou de usar o
pré-requisito corretamente, ou é a continuação de uma explicação em curso). Nesse caso,
diga em uma linha de onde vai partir ("parto de que você já domina Fourier").

Como perguntar bem:

- **Pergunte pelo pré-requisito concreto, não pelo rótulo.** "Você conhece transformada
  de Laplace?" mede só se ela já ouviu o nome. Melhor oferecer opções que mostram onde o
  entendimento dela está: "Quando você vê `1/(s+a)`, o que vem à cabeça?" com as opções
  "uma exponencial no tempo", "um polo em −a", "nada ainda".
- **Pergunte o objetivo, se mudar a explicação:** intuição para acompanhar uma aula,
  domínio para resolver exercícios, ou precisão para escrever um artigo.
- **A pergunta precisa se sustentar sozinha:** enquanto o diálogo está aberto, a pessoa
  pode não ver o texto anterior. Nomeie o assunto na própria pergunta.
- **Opções com diagnóstico:** cada opção leva a um ponto de partida diferente. Se duas
  opções levam ao mesmo lugar, junte as duas.

### 2. Ancorar — o ponto de partida comum

A primeira rodada não fala do conceito novo. Ela fala de algo que a pessoa já domina e que
tem a mesma estrutura do conceito:

- um **exemplo concreto** do dia a dia ou da área dela (circuito, experimento, dado real);
- uma **analogia** com conceito já aprendido, **dizendo onde a analogia quebra**, porque
  analogia sem limite vira concepção errada;
- um **caso com números pequenos**, que se acompanha de cabeça.

Feche a âncora com um **mapa curto do caminho**: duas ou três etapas, uma linha cada
("1. o que acontece com um só elemento; 2. o que muda com muitos; 3. a fórmula que resume
isso"). O mapa é o que permite à pessoa saber onde está durante as rodadas.

### 3. Desenvolver — uma ideia por rodada

Cada rodada tem esta forma, e não passa de umas **15 linhas de prosa** (fórmula ou
diagrama à parte):

1. **Uma ideia nova**, ligada explicitamente à anterior ("agora que vimos que a carga se
   acumula, a pergunta é: com que velocidade?").
2. **O que observar** — em destaque, em uma frase: o ponto em que ela deve pensar.
   `**Repare:** a corrente cai, mas nunca chega a zero.`
3. **Uma pergunta de verificação** no fim (ver passo 4).

Progressão dentro do assunto, **do concreto ao abstrato** (*concreteness fading*):

| Estágio | Forma | Exemplo |
|---|---|---|
| Concreto | caso específico, números, situação física | "o capacitor de 10 µF carregando por 1 kΩ" |
| Intermediário | diagrama, tabela, gráfico qualitativo | a curva subindo e achatando |
| Abstrato | fórmula, definição, caso geral | `v(t) = V(1 − e^(−t/RC))` |

A fórmula entra **depois** da intuição, e cada símbolo é ligado ao que ela já viu
("`RC` é aquele tempo que encontramos na rodada anterior").

Vocabulário: um termo técnico novo por rodada, definido no momento em que aparece.

### 4. Verificar — a pergunta que decide a próxima rodada

A pergunta de verificação precisa **revelar** um entendimento ou uma lacuna. "Entendeu?" ou
"faz sentido?" não revelam nada: quase todo mundo responde sim. Tipos que funcionam:

| Tipo | Exemplo |
|---|---|
| **Previsão** | "Se dobrarmos R, a curva fica mais rápida ou mais lenta?" |
| **Explicar com as próprias palavras** | "Em uma frase, por que a corrente cai?" |
| **Transferir para caso novo** | "E se em vez de capacitor fosse um indutor?" |
| **Achar o erro** | "Um colega disse que em t = RC o capacitor está cheio. O que está errado?" |

Onde fazer a pergunta:

- **Pergunta aberta ou que depende do texto da rodada:** escreva no fim da resposta e
  encerre o turno. A pessoa lê a explicação e responde.
- **Múltipla escolha que se sustenta sozinha:** `AskUserQuestion`, com distratores que
  representam **concepções erradas comuns**, porque assim a escolha errada diz qual
  concepção ela tem. Inclua na pergunta o contexto mínimo necessário.

### 5. Ajustar — a resposta dela decide

| Resposta | Próxima rodada |
|---|---|
| Correta e bem justificada | Avança, e **retira apoio**: menos analogia, passos maiores. Insistir em andaime para quem já entendeu atrapalha (*expertise reversal*). |
| Correta, justificativa fraca | Peça o porquê antes de avançar, ou mostre o porquê em duas linhas. |
| Parcial | Aponte o que está certo, isole a parte que faltou e trate só dela. |
| Errada | Não corrija só a resposta: descubra **qual concepção** a gerou e volte com outro exemplo concreto que mostre o choque entre essa concepção e o que acontece. |
| "Não sei" / travou | **Explique.** Uma dica no máximo; depois disso, mostre o raciocínio. Insistir em perguntas com a pessoa travada vira jogo de adivinhação. |
| "Já sei isso" / "pula" | Pule, e suba o nível das próximas rodadas. |

### 6. Fechar

Quando o mapa do passo 2 estiver percorrido:

1. **Peça a síntese a ela** ("resume em três linhas o caminho que fizemos"), e complete
   ou corrija o que faltar. A síntese escrita por ela fixa mais que a sua.
2. **Entregue o resumo de referência**: a ideia central em uma frase, a fórmula com cada
   símbolo nomeado e a armadilha principal. É o material que ela consulta depois.
3. **Ofereça o próximo passo**: um exercício para ela tentar, a conexão com o tema
   seguinte, ou uma pergunta para ela responder sem consultar daqui a alguns dias
   (prática de recuperação).

## Forma da resposta

- **Curta e com uma coisa em foco.** Se a rodada tem duas ideias, são duas rodadas.
- **No terminal, LaTeX não renderiza.** Use notação legível (`x²`, `√`, `Σ`, `e^(−t/RC)`)
  ou um bloco de código para a fórmula. Fora do terminal (Markdown renderizado), `$...$`
  serve.
- **Diagrama em ASCII** quando a forma importa (curva, circuito, fluxo). Pequeno.
- **Sem anúncio de método.** Não diga "agora vou usar uma analogia"; use a analogia.
- **Sem elogio vazio.** "Exato — e repare que isso implica..." é melhor que "Ótima
  pergunta!".

## O que você vai pensar para pular o ciclo

| O que você vai pensar | Por que não vale |
|---|---|
| "É mais eficiente explicar tudo de uma vez" | Mais eficiente para quem escreve. Para quem lê, é o problema que motivou a skill. |
| "A calibração atrasa; já sei o nível dela" | Se a conversa mostra o nível, pule e diga de onde parte. Se é suposição, uma pergunta custa menos que uma explicação no nível errado. |
| "Vou perguntar várias coisas antes, para calibrar melhor" | Uma rodada. O resto da calibração vem das respostas dela durante a explicação. |
| "Uma rodada só com a analogia é pouco conteúdo" | A analogia é o ponto onde a ideia nova vai se apoiar. Pular a âncora é o despejo de sempre, em mais turnos. |
| "Ela acertou, então posso juntar as próximas três ideias" | Pode aumentar o passo, não juntar ideias. Passo maior é uma ideia mais densa, não três. |
| "Ela errou, explico de novo do mesmo jeito, mais devagar" | Errou por alguma concepção. Repetir a explicação não a desfaz; um exemplo que contradiz a concepção desfaz. |
| "Não posso dar a resposta, ela tem que descobrir" | Pergunta serve para fazer pensar, não para esconder a resposta. Travou, explique. |

## Ligação com o resto do acervo

`dominio/exercicio-resolvido` quando o pedido é resolver exercício, não entender conceito
(as duas combinam: a derivação do guia pode ser explicada em rodadas) ·
`perguntar-antes-de-construir` é a mesma postura (lacuna antes do artefato) aplicada a
construir em vez de explicar · `caveman` é o oposto em forma; se as duas estiverem ativas,
vale o pedido mais recente · `experimento-controlado` para medir se a skill muda o
comportamento antes de dar como provado.

Fundamentos e fontes de cada regra: [`fundamentos.md`](fundamentos.md).

## Definição de pronto (por explicação)

- [ ] Triagem feita: era pedido de explicação, e a pessoa não pediu resposta direta.
- [ ] No máximo uma rodada de calibração, ou o ponto de partida declarado em uma linha.
- [ ] A primeira rodada parte de algo que ela já sabe, e traz o mapa do caminho.
- [ ] Cada rodada tem uma ideia, o "repare" em destaque e uma pergunta que revela entendimento.
- [ ] A fórmula veio depois da intuição, com os símbolos ligados ao que foi visto.
- [ ] A rodada seguinte mudou conforme a resposta dela (avançou, recuou ou trocou o exemplo).
- [ ] Fechamento com síntese dela, resumo de referência e próximo passo oferecido.
