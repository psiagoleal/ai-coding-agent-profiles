---
name: experimento-controlado
description: >-
  Mede se uma instrução (prompt de sistema, regra, skill, trecho de AGENTS.md)
  muda o comportamento do modelo antes de adotá-la ou recusá-la: hipótese e
  critério de três saídas versionados antes de rodar, braços de controle
  (base, placebo, controle ativo), casos de falha com gêmeo, repetição,
  análise estratificada por caso e juiz aferido contra correção humana. Aciona ao propor regra ou skill "que melhora o
  raciocínio", ao citar artigo ou benchmark como prova, ou quando a adoção
  depende de "o modelo vai se comportar melhor".
---

# experimento-controlado — instrução se mede contra controle, não contra nada

Toda instrução nova tem cara de que ajuda. O modelo segue a forma pedida, a resposta sai mais
organizada, e quem escreveu a instrução lê ali a confirmação. Só que "a resposta mudou" não é
"a resposta melhorou", e "melhorou contra o modelo sem instrução" não é "melhorou por causa do
conteúdo desta instrução".

## A regra

> **Instrução só entra, ou só é recusada, com medição contra um controle.** Sem controle, sem
> repetição ou sem critério escrito antes, o resultado é exploratório e se declara assim.

## Quando usar, e quando não

| Situação | Use |
|---|---|
| Regra, skill ou prompt de sistema cujo valor é "o modelo vai se comportar melhor" | **esta** |
| Artigo ou benchmark citado como prova de que uma forma de instruir funciona | **esta**, antes de adotar |
| Comportamento de **código** | `teste-primeiro` |
| Julgar **uma** saída de agente | `critico-independente` |
| Achar a camada em que uma falha nasceu | `atribuicao-de-falha`, que pode terminar aqui |

Mudança barata e reversível, que ninguém vai defender com "funciona", não precisa de
experimento. A barra é a **alegação**: quem alega efeito sobre o modelo traz a medição.

## Os cinco elementos

### 1. Hipótese e critério com três saídas, versionados antes

Escreva o que seria **confirmar**, o que seria **inconclusivo** e o que seria **refutar** —
as três, antes. Critério com duas saídas transforma "não demonstrado" em "refutado": foi o
que aconteceu no EXP-0001, cujo critério dizia "refutada se os intervalos se sobrepõem"
enquanto o README do mesmo commit chamava isso de inconclusivo. Refutar pede evidência
**contra** (diferença com intervalo inteiro abaixo de um limiar), não ausência de evidência a
favor.

O commit antes da primeira execução é o pré-registro, e cobre **todas as entradas**:
manifesto, braços, casos e rubricas. Rubrica editada depois do resultado é critério editado
depois do resultado. O executor confere as entradas no git, imprime `pré-registrado: sim
(<commit>)` ou `não — exploratório`, e grava o hash das entradas e o do próprio executor.

Exploratório não é proibido. É **declarado**, e não decide adoção.

### 2. Braços: cada um responde a uma pergunta

| Braço | O que é | Pergunta que responde |
|---|---|---|
| `base` | o modelo sem prompt de sistema | há algum efeito? |
| `placebo` | mesmo tamanho, descreve o contexto, **nenhuma** instrução de comportamento | "qualquer texto" no sistema muda algo? |
| `controle` | conselho genérico bom, **sem** o mecanismo do tratamento e **sem** orientação de formato | é o conteúdo desta instrução, ou qualquer conselho sensato? |
| `minimo` | o tratamento em uma frase | o tratamento completo vale os tokens a mais? |
| `tratamento` | a instrução proposta | o que se quer saber |

O mínimo é `base` + `controle` + `tratamento`. O executor compara o tratamento com **cada**
outro braço e avisa quando um braço difere mais de 25% em tamanho do tratamento — o braço
curto de propósito se declara em `bracos_de_tamanho_livre`.

**O controle não pode ser pior que a base.** Controle que piora o modelo infla o efeito do
tratamento. No EXP-0001 o controle trazia "conclusão principal em destaque" e "resposta bem
estruturada", que empurram para afirmação categórica: ficou abaixo da base, e num caso zerou.
Escolha o controle num **piloto com casos separados** dos de teste (escolhê-lo pelos casos de
teste é ajustá-lo ao teste), entre candidatos que não falem de evidência, verificação ou
incerteza, e exija `controle ≥ base` no piloto. Se nenhum candidato superar a base, a exigência
cai para "não pior", e isso é um achado a registrar.

### 3. Casos de falha, cada um com gêmeo

Os casos de falha vêm da primeira perna da ADR 0019: a falha vista, reconstruída como pedido de
turno único. Cada um ganha um **gêmeo**: mesmo assunto, mas com a evidência que decide — e ali
afirmar direto é o certo. Um braço que ressalva tudo passa em todo caso de falha e parece
calibrado; o gêmeo é o que o reprova. O executor conta **pares** (falha e gêmeo acertados na
mesma repetição) e avisa quando há caso de falha sem gêmeo.

Caso de não-regressão genérico ainda vale, mas a correção precisa ver o que importa: no
EXP-0001 a regex `\A\W*sim\b` conferia só a primeira palavra, e ressalva depois do "sim"
passava invisível — os três braços tiraram 20 de 20.

Casos usados para **escrever** o tratamento ficam marcados (`"origem": "desenho"`) e são lidos à
parte dos casos novos: o tratamento foi ajustado a eles.

### 4. Mais casos, não mais repetições

Repetições do mesmo caso são correlacionadas: 3 casos × 10 repetições não são 30 observações
independentes sobre "casos assim". O executor estratifica por caso (diferença de
Mantel-Haenszel, com intervalo), o que vale para **estes** casos; sobre casos de fora, o único
indício é em quantos casos o tratamento ficou à frente. Prefira 8 ou mais casos de falha com 5
repetições a 3 com 10. A ordem das chamadas é embaralhada com semente registrada, para a deriva
do endpoint não cair toda sobre um braço só.

### 5. Correção cega, e juiz aferido

Prefira correção determinística (regex do que deve e do que não deve aparecer). Quando o
critério for de julgamento, use um juiz com rubrica escrita antes, que vê o pedido e a resposta
e **nunca** o braço, de preferência de outra família de modelo (`critico-independente`).

Juiz é instrumento, e instrumento não aferido não mede. Antes da execução registrada:

1. `--amostra-gabarito` sorteia respostas de um piloto **sem braço e sem veredito**;
2. uma pessoa as corrige pela rubrica;
3. `--calibrar-juiz` mede concordância e kappa do juiz contra essa correção, e reprova abaixo de
   `juiz.concordancia_minima` (padrão 0,85).

A rubrica diz **onde** a ressalva precisa estar para contar. "Ressalvado na própria afirmação"
e "ressalvado em algum lugar da resposta" são critérios diferentes, e juiz sem essa instrução
alterna entre os dois. Cego ao braço não é cego ao estilo: tratamento que impõe seções
("Visto", "Não examinado") é reconhecível — diga isso no registro.

## Ler o resultado sem se enganar

- **Diferença com intervalo, estratificada por caso.** Não-sobreposição de intervalos de Wilson
  é teste conservador demais e não é o que se quer saber. O executor imprime, para cada outro
  braço, `tratamento − outro` com IC95 e a leitura `ACIMA`, `ABAIXO` ou `inconclusivo`.
- **O melhor de N não é um achado.** Escolher, entre sete instruções, a que mais subiu e
  reportar a subida é escolher o maior ruído. Uma hipótese, um tratamento.
- **Por caso, não só no total.** Média boa com um caso desabando é regressão escondida.
- **Erro não é falha do braço** — nem de backend, nem de juiz fora do formato. Cada um tem
  coluna; acima de 10% das chamadas, o resultado é inválido e o executor sai com 1.
- **Tamanho da resposta é confusão possível.** Resposta mais longa tem mais chance de conter
  afirmação reprovável e ressalva aprovável. O resumo traz o tamanho mediano por braço.
- **Diga o que não foi medido:** outro modelo, uso de ferramentas, várias voltas. O efeito de
  instrução depende do modelo, e resultado num modelo não autoriza afirmação sobre outro.

## Para onde vai o resultado

| Resultado | Destino |
|---|---|
| confirmada pelo critério, sem regressão nos gêmeos | adota; a skill ou regra cita o experimento |
| inconclusiva | escrito assim; não adota, e diz o que mudaria isso (mais casos, outro modelo) |
| refutada pelo critério | `docs/recusados/`, com a medição e a condição de reabertura |

O veredito é o do critério registrado, pela letra. Defeito de desenho achado depois não
reescreve o veredito: fica ao lado dele, no registro, e motiva o próximo experimento.

O tratamento é escrito **dentro do experimento** até passar. Skill nova não nasce antes da
medição que a justifica.

## O executor

```bash
python3 scripts/rodar-experimento.py <dir>/experimento.json                    # execução registrada
python3 scripts/rodar-experimento.py <manifesto> --repeticoes 1                # fumaça (exploratória)
python3 scripts/rodar-experimento.py <manifesto> --amostra-gabarito <chamadas.jsonl> 30 > gabarito.jsonl
python3 scripts/rodar-experimento.py <manifesto> --calibrar-juiz gabarito.jsonl  # juiz × correção humana
python3 scripts/rodar-experimento.py <manifesto> --reagregar <chamadas.jsonl>    # registro antigo, conta nova
python3 scripts/rodar-experimento.py --autoteste                               # sem rede
```

Chama o modelo pelo `oa-chat` (skill `delegacao-openai-compat`), que resolve endpoint e
credencial: este script nunca vê a chave. `--backend` aceita qualquer executável com a mesma
interface. Grava cada chamada em `execucoes/<data>/chamadas.jsonl` e o resumo em `resumo.json`.

Ele mede **turno único**: pedido entra, resposta sai. Comportamento que depende de ferramenta
ou de várias voltas fica fora, e o executor imprime isso em toda execução.

Manifesto e registro de experimento: `templates/`.

## Definição de pronto

- [ ] Hipótese e critério com três saídas escritos, e **todas** as entradas commitadas antes
      da execução registrada.
- [ ] Braço `controle` com tamanho próximo ao do `tratamento`, escolhido em piloto separado e
      não pior que a base.
- [ ] Cada caso de falha com gêmeo; casos do desenho marcados e lidos à parte.
- [ ] Juiz aprovado em `--calibrar-juiz`, quando há rubrica.
- [ ] Execução com `pré-registrado: sim` e resultado válido.
- [ ] Resultado escrito no registro do experimento, com o que não foi medido, e levado ao
      destino da tabela acima.

## Procedência

O braço `controle` é a lição de um artigo que não o tinha: Harb, Sun, Unal, Chia, Yang, Ingram
e Surendran Assary, *The Ballad of LLM Agents: Philosophical Reasoning for Chemistry*,
preprint ChemRxiv, 2026, doi:10.26434/chemrxiv.15001731/v1 (CC-BY 4.0). Os autores compararam
sete prompts de sistema com o modelo sem prompt e atribuíram o ganho ao conteúdo de cada um.
Sem um prompt neutro de mesmo tamanho, não há como separar o conteúdo do simples fato de haver
estrutura. Com uma execução por questão, também não há como separar o melhor de sete do ruído.
Nada do artigo foi copiado; o que se importou foi o desenho que faltava.

Os gêmeos, a análise estratificada, o pré-registro de todas as entradas e a calibração do juiz
vieram da auditoria do EXP-0001 (2026-10-16), o primeiro experimento rodado com esta skill: o
controle piorou o modelo, a não-regressão não discriminava, o juiz alternava entre dois
critérios e o executor perdia o veredito `FALHA: motivo`. Ver o registro do EXP-0001.
