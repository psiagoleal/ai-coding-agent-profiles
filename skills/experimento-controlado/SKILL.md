---
name: experimento-controlado
description: >-
  Mede se uma instrução (prompt de sistema, regra, skill, trecho de AGENTS.md)
  muda o comportamento do modelo antes de adotá-la ou recusá-la: hipótese e
  critério de refutação versionados antes de rodar, três braços (base,
  controle do mesmo tamanho, tratamento), casos tirados de falha observada,
  repetição e correção cega. Aciona ao propor regra ou skill "que melhora o
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

### 1. Hipótese e critério de refutação, versionados antes

Escreva o que seria **refutar**, não só o que seria confirmar: "a hipótese cai se o tratamento
não ficar acima do controle com intervalos separados, ou se ficar abaixo nos casos de
não-regressão". O commit do manifesto antes da primeira execução é o pré-registro: prova que o
critério veio antes do resultado. O executor confere isso e imprime `pré-registrado: sim
(<commit>)` ou `não — exploratório`.

Exploratório não é proibido. É **declarado**, e não decide adoção.

### 2. Três braços, e o do meio é o que importa

| Braço | O que é | O que separa |
|---|---|---|
| `base` | o modelo sem a instrução | se há algum efeito |
| `controle` | instrução **neutra, do mesmo tamanho** ("seja cuidadoso, pense passo a passo") | o efeito de **ter** instrução do efeito **desta** instrução |
| `tratamento` | a instrução proposta | o que se quer saber |

Sem o controle, a comparação mede "qualquer texto a mais no sistema". O executor avisa quando
controle e tratamento diferem mais de 25% em tamanho.

### 3. Casos tirados de falha observada, e casos de não-regressão

Os casos de falha vêm da primeira perna da ADR 0019: a falha vista, reconstruída como pedido
de turno único. Os de **não-regressão** são pedidos que a instrução **não** deveria mudar, ou
que ela pode piorar (excesso de ressalva, recusa a responder o que a evidência já responde).
Instrução que conserta um caso e estraga três não passa, e só o caso de não-regressão mostra
isso.

### 4. Repetição e ordem embaralhada

Uma execução por caso não separa efeito de sorte. Comece com 10 repetições por caso e por
braço. A ordem das chamadas é embaralhada com semente registrada, para a deriva do endpoint ao
longo do tempo não cair toda sobre um braço só.

### 5. Correção cega

Prefira correção determinística (regex do que deve e do que não deve aparecer). Quando o
critério for de julgamento, use um juiz com rubrica escrita antes, que vê o pedido e a
resposta e **nunca** o braço. De preferência, de outra família de modelo (`critico-independente`).

## Ler o resultado sem se enganar

- **Taxa com intervalo, nunca taxa sozinha.** O executor imprime o intervalo de Wilson a 95%.
  Com 30 chamadas por braço, 60% e 75% não se distinguem.
- **O melhor de N não é um achado.** Escolher, entre sete instruções, a que mais subiu e
  reportar a subida é escolher o maior ruído. Uma hipótese, um tratamento.
- **Por caso, não só no total.** Média boa com um caso desabando é regressão escondida.
- **Erro de backend não é falha do braço.** Conta à parte; acima de 10% das chamadas, o
  resultado é inválido e o executor sai com 1.
- **Diga o que não foi medido:** outro modelo, uso de ferramentas, várias voltas. O efeito de
  instrução depende do modelo, e resultado num modelo não autoriza afirmação sobre outro.

## Para onde vai o resultado

| Resultado | Destino |
|---|---|
| tratamento acima do controle, sem regressão | adota; a skill ou regra cita o experimento |
| intervalos se sobrepõem | **inconclusivo** — escrito assim; não adota, e diz o que mudaria isso (mais casos, outro modelo) |
| tratamento igual ou abaixo do controle | `docs/recusados/`, com a medição e a condição de reabertura |

O tratamento é escrito **dentro do experimento** até passar. Skill nova não nasce antes da
medição que a justifica.

## O executor

```bash
python3 scripts/rodar-experimento.py <dir>/experimento.json            # execução registrada
python3 scripts/rodar-experimento.py <manifesto> --repeticoes 1        # fumaça (exploratória)
python3 scripts/rodar-experimento.py --autoteste                       # sem rede
```

Chama o modelo pelo `oa-chat` (skill `delegacao-openai-compat`), que resolve endpoint e
credencial: este script nunca vê a chave. `--backend` aceita qualquer executável com a mesma
interface. Grava cada chamada em `execucoes/<data>/chamadas.jsonl` e o resumo em `resumo.json`.

Ele mede **turno único**: pedido entra, resposta sai. Comportamento que depende de ferramenta
ou de várias voltas fica fora, e o executor imprime isso em toda execução.

Manifesto e registro de experimento: `templates/`.

## Definição de pronto

- [ ] Hipótese e critério de refutação escritos e commitados antes da execução registrada.
- [ ] Braço `controle` com tamanho próximo ao do `tratamento`.
- [ ] Casos de falha **e** casos de não-regressão.
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
