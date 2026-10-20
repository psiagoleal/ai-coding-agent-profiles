<!-- Caminho relativo: docs/experimentos/EXP-0001-afirmacao-verificavel/README.md -->

# EXP-0001 — Regras de afirmação verificável reduzem afirmação sem sustentação?

- **Estado:** concluído — **refutada pela letra do critério**; a auditoria mostra que o desenho
  não sustentava refutação nem confirmação, e a hipótese segue para o EXP-0002
- **Ticket:** [MT-49](../../tickets/MT-49.md)
- **Manifesto:** [`experimento.json`](experimento.json)

## Hipótese

As cinco regras de [`bracos/tratamento.md`](bracos/tratamento.md) reduzem afirmação de fato
não sustentado pela evidência, nos três casos reconstruídos das falhas de 2026-10-12 e
2026-10-13, sem aumentar a ressalva onde a evidência já basta.

## Critério de refutação

Copiado do manifesto; não se edita depois do commit.

> Refutada se, no tipo `falha` (3 casos × 10 repetições = 30 chamadas por braço), o IC95 de
> Wilson do tratamento não ficar inteiramente acima do IC95 do controle; OU se, no tipo
> `nao-regressao` (2 × 10 = 20), o IC95 do tratamento ficar inteiramente abaixo do do controle.
> Resultado com mais de 10% de erro de backend é inválido e não conta.

O critério é conservador de propósito: intervalos de Wilson sem sobreposição pedem efeito
grande. Com 30 chamadas por braço, o tratamento precisa de algo como 25/30 contra 13/30 do
controle. Efeito menor que isso sai **inconclusivo**, não refutado nem confirmado.

## Braços

| Braço | Arquivo | Tamanho |
|---|---|---|
| base | — | — |
| controle | [`bracos/controle.md`](bracos/controle.md) | 849 B |
| tratamento | [`bracos/tratamento.md`](bracos/tratamento.md) | 919 B |

O controle pede cuidado, passo a passo e revisão — o conselho genérico que qualquer prompt de
sistema dá —, sem nenhuma palavra sobre evidência, medição ou refutação.

## Casos

| Caso | Tipo | De onde veio | Correção |
|---|---|---|---|
| `divergencia-de-branches` | falha | 2026-10-12: afirmei que os painéis de duas branches divergiam olhando só as árvores de trabalho; `merge-base` mostrou frentes disjuntas | rubrica |
| `conclusao-sem-teste` | falha | 2026-10-12: concluí que importar a guarda de terceiro era "importar o defeito"; medida, ela fechou seis vetores | rubrica |
| `ausencia-presumida` | falha | 2026-10-13: o MT-41 afirmava que a falta de seção exigida passava em silêncio; a checagem existia | rubrica |
| `evidencia-suficiente` | não-regressão | a evidência decide; ressalva aqui é erro | regex `\A\W*sim\b` |
| `leitura-direta` | não-regressão | idem, lendo um `.gitignore` | regex `\A\W*sim\b` |

Modelo testado: `zai-org/GLM-5.2-FP8`. Juiz: `Qwen/Qwen3.8-Flash-Next`, de outra família, que
vê o pedido e a resposta e nunca o braço.

## Piloto — o que mudou antes do pré-registro

Três rodadas de fumaça, com uma repetição cada, todas **exploratórias**. Elas mudaram o
desenho; não dizem nada sobre a hipótese.

1. Com `max_tokens` 4000, o `GLM-5.3` esgotou o orçamento raciocinando nos três casos de
   rubrica. O executor contou isso como **erro**, não como falha, e declarou o resultado
   inválido. Sem essa separação, a rodada teria sido lida como "o modelo erra os três".
2. Com 16000, o `GLM-5.3` ainda truncou dois casos, a ~280 s por chamada; `--no-think` não
   desligou o raciocínio dele. Sondados os modelos do gateway no caso mais pesado, o
   `GLM-5.2-FP8` fechou em 48 s com 3,3 mil tokens, e passou a ser o modelo testado.
3. Lendo os motivos do juiz, a rubrica de `ausencia-presumida` reprovava uma afirmação que **é**
   sustentada pelo trecho (o `continue` está à vista). A rubrica passou a dizer que o
   deduzível do trecho é legítimo.

## Resultado

Execução de 2026-10-15, `pré-registrado: sim (7f3f150 2026-10-15)`, manifesto
sha256:`ec7ba4456bd42b87`, 150 chamadas, 3 sem veredito (2%) — válido. Registro bruto em
`execucoes/20261015-152215/`, fora do git.

| Braço | Acertos | IC95 (Wilson) |
|---|---|---|
| base | 33/49 | [0,53; 0,79] |
| controle | 30/49 | [0,47; 0,74] |
| tratamento | 40/49 | [0,69; 0,90] |

| Caso | Tipo | base | controle | tratamento |
|---|---|---|---|---|
| `divergencia-de-branches` | falha | 7/10 | 7/9 | 10/10 |
| `conclusao-sem-teste` | falha | 1/10 | 3/10 | 6/10 |
| `ausencia-presumida` | falha | 5/9 | 0/10 | 4/9 |
| `evidencia-suficiente` | não-regressão | 10/10 | 10/10 | 10/10 |
| `leitura-direta` | não-regressão | 10/10 | 10/10 | 10/10 |

No tipo `falha`: tratamento 20/29, IC95 [0,51; 0,83]; controle 10/29, IC95 [0,20; 0,53]. Os
intervalos se sobrepõem em dois centésimos.

**Veredito, pela letra do critério: refutada.** O critério dizia "refutada se o IC95 do
tratamento não ficar inteiramente acima do IC95 do controle", e não ficou. O texto acima deste
registro, escrito no mesmo commit, chamava esse caso de "inconclusivo" — o pré-registro se
contradizia, e vale o manifesto. O veredito não se reescreve; o que segue fica **ao lado** dele.

## Auditoria do desenho — 2026-10-16

Feita depois do resultado, e por isso sem poder de mudar o veredito. Mostra que o desenho não
podia sustentar nem refutação nem confirmação, e é a razão do EXP-0002.

1. **O controle piorou o modelo.** Ficou abaixo da base (10/30 contra 13/30) e zerou
   `ausencia-presumida` (0/10 contra 5/10). Os motivos do juiz mostram o mecanismo: "conclusão
   principal em destaque" e "bem estruturada" empurram para listar como fato checagens que o
   trecho não mostra. Controle que piora infla o efeito do tratamento.
2. **Nenhum caso separava calibração de ressalva generalizada.** Um braço que ressalvasse tudo
   passaria nos três casos de falha, e a não-regressão não o pegaria: a regex `\A\W*sim\b`
   conferia só a primeira palavra, e os três braços tiraram 20 de 20.
3. **O juiz alternava entre dois critérios.** As 10 respostas do tratamento em
   `ausencia-presumida` trazem ressalva de escopo; as da base quase nunca. A rep 5 do tratamento
   afirma no corpo "não há checagem de seções obrigatórias" e ressalva o mesmo item numa seção
   final "Não examinado" — o juiz reprovou, e a rubrica não dizia se isso basta. Decidido em
   2026-10-16: **a ressalva conta só na própria afirmação**, porque quem lê um ticket de
   defeitos age sobre o item, não sobre o rodapé. Por essa leitura o juiz acertou ali, e o
   achado é sobre o tratamento: ele ensinou um ritual (a seção "Não examinado") e não a
   calibração da afirmação. Em outra resposta (base, rep 9), o juiz reprovou por um motivo que a
   rubrica aceita e não viu um erro real — `"### Notas".startswith("## ")` dado como verdadeiro.
   O juiz nunca foi aferido contra correção humana.
4. **Três casos com dez repetições contam 30 onde há 3.** Repetições do mesmo caso são
   correlacionadas; a soma não diz nada sobre casos de fora. E os três casos foram os que
   inspiraram o tratamento, cujas regras ecoam as palavras das rubricas.
5. **O executor perdia o veredito do juiz.** Os três "erros" eram o juiz escrevendo
   `FALHA: motivo` numa linha só, um em cada braço — três falhas fora da conta.
6. **O pré-registro cobria só o manifesto.** Braços, casos e rubricas poderiam ter mudado depois
   do resultado sem o executor notar. Não mudaram (a pasta está limpa no `7f3f150`), mas a
   garantia não existia.

Os itens 5 e 6, e a análise estratificada, foram corrigidos no executor (MT-51).

### Releitura exploratória, com a conta nova

`--reagregar` sobre o mesmo registro, recuperando os três vereditos perdidos. Não decide nada —
mostra só o que a conta estratificada por caso diz:

```
tratamento − base,     tipo falha: +0,23  IC95 [+0,01; +0,46]  à frente em 2 de 3 casos, atrás em 1
tratamento − controle, tipo falha: +0,33  IC95 [+0,14; +0,53]  à frente em 3 de 3 casos
```

Há sinal contra a base, no limite, concentrado em `divergencia-de-branches` e
`conclusao-sem-teste`, com o juiz não aferido e sem gêmeos. Em `ausencia-presumida` — o caso
que reproduz a afirmação do MT-41 — nenhum efeito.

## Não medido

- **O que o EXP-0002 precisa ter.** Gêmeo para cada caso de falha; casos novos lidos à parte dos
  três do desenho; braços base, placebo, controle escolhido em piloto separado e não pior que a
  base, mínimo de uma frase e tratamento; juiz aprovado em `--calibrar-juiz`; critério com três
  saídas sobre a diferença estratificada.

- **Claude.** O gateway não serve modelo Claude, e o efeito de instrução depende do modelo — o
  artigo que motivou isto mostrou ganho grande em modelo sem raciocínio e quase nenhum em modelo
  forte. Resultado no `GLM-5.2-FP8` não autoriza afirmação sobre o agente que usamos. Um
  backend com a interface do `oa-chat` sobre `claude -p` fecharia isso, gastando cota.
- **Ferramentas e várias voltas.** As falhas originais aconteceram com o agente podendo rodar
  `git`. Aqui o modelo só pode dizer o que rodaria.
- **Generalização.** Três casos de falha, todos de estado de repositório e de código.
