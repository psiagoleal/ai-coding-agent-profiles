---
name: delegacao-openai-compat
description: >-
  Delega trabalho de volume a um modelo servido por qualquer endpoint
  OpenAI-compatible (gateway LiteLLM, vLLM, Ollama em /v1, LM Studio, OpenRouter)
  para que o custo saia da cota da assinatura e a saída não ocupe o contexto da
  sessão. Traz o script `oa-chat` (chamada direta, sem chave em argv) e a rota
  via `agentry` para modo agente. Cobre a checagem de egresso obrigatória, a
  resolução da chave sem expô-la, modelos de raciocínio que esgotam tokens, o
  pedido autocontido e a verificação do resultado. Aciona quando o usuário pedir
  para "delegar ao gateway", "usar o LiteLLM", "usar modelo OpenAI-compatible",
  "rodar num modelo mais barato", "economizar limite" ou "economizar cota"; ao
  planejar varredura, revisão ou extração volumosa; ou ao configurar
  `providers.litellm` e task-class de delegação no `agentry`.
---

# delegacao-openai-compat — gastar token de endpoint em vez de cota de assinatura

## A regra

> **Nada sai para um endpoint sem egresso conhecido. E nada que volta de lá é usado sem
> verificação.**

Delegar economiza cota; não transfere responsabilidade. O endpoint é um modelo que você não
escolheu, com qualidade que você não mediu, atrás de uma rota que talvez termine na nuvem
pública.

## Por que "OpenAI-compatible" e não "LiteLLM"

A API de *chat completions* da OpenAI virou o protocolo comum: LiteLLM, vLLM, SGLang, Ollama
(em `/v1`), LM Studio, OpenRouter e a própria OpenAI falam o mesmo formato. O que esta skill
ensina vale para todos. Nenhum endereço, chave ou nome de modelo mora neste repositório —
tudo vem do ambiente.

"Compatível", porém, cobre o **núcleo** do protocolo. Fora dele, cada servidor diverge:

| Recurso | Comportamento real |
|---|---|
| `messages`, `temperature`, `max_tokens` | Universal |
| `response_format: json_object` | Comum, não universal — confira a saída mesmo assim |
| Campo de raciocínio (`reasoning_content`) | Não é OpenAI; aparece em vLLM/SGLang com modelos de raciocínio |
| Desligar raciocínio | Específico da **implantação**, não do modelo: `chat_template_kwargs.enable_thinking=false` (vLLM/SGLang) ou `thinking: {"type": "disabled"}` (formato Anthropic/Z.ai, repassado por alguns proxies); `reasoning_effort` pode ser **ignorado** em silêncio. Ver [Desligar o raciocínio](#desligar-o-raciocínio-a-chave-depende-da-implantação) |
| Tool-calling | Varia muito por modelo e servidor — não presuma |
| Campo desconhecido no corpo | Uns ignoram, outros respondem `400` |

## Antes de tudo: a checagem de egresso

Um endpoint pode estar na sua rede e **ainda assim encaminhar tudo para a nuvem pública**.
O destino efetivo dos dados não é o host do proxy.

1. **Para onde este endpoint roteia?** Modelos hospedados internamente, endpoint corporativo,
   nuvem pública?
2. **Os backends têm opt-out de retenção e treino?** Sem isso, nada sob NDA sai (§0 e §7 do
   `AGENTS.md`).
3. **Quem opera o endpoint declarou a classe?** No `agentry`, isso é o `egressClass`; fora
   dele, é uma resposta explícita de quem opera.

Qualquer "não sei" ⇒ **não delegue material do cliente**. Delegue só o que já seria público,
ou use a rota local da skill `delegacao-a-subagentes`.

## Configuração — só pelo ambiente

| Variável | Papel | Fallback |
|---|---|---|
| `OPENAI_COMPAT_BASE_URL` | Endpoint, com ou sem `/v1` | `AGENTRY_LITELLM_BASE_URL` |
| `OPENAI_COMPAT_API_KEY` | Chave; vazia = endpoint sem autenticação | `AGENTRY_LITELLM_API_KEY` |
| `OPENAI_COMPAT_KEY_CMD` | Comando que imprime a chave (`op read …`, `pass …`) | — |
| `OPENAI_COMPAT_KEY_FILE` | Arquivo cuja 1ª linha é a chave | — |
| `OPENAI_COMPAT_MODEL` | Modelo padrão; sem ele, `-m` é obrigatório | — |

⚠️ **Não use `OPENAI_BASE_URL`/`OPENAI_API_KEY` para isto.** São lidas automaticamente pelos
SDKs oficiais e por várias CLIs. Exportá-las globalmente apontando para um gateway interno
redireciona em silêncio **outras** ferramentas da máquina — inclusive com a chave errada.

A chave segue a `secrets-guard` e a exceção de segredo da ADR 0011: fora do repositório,
nunca em argumento de comando, nunca ecoada. Para conferir presença sem expor:

```bash
python3 -c "import os; v=os.environ.get('OPENAI_COMPAT_API_KEY') or os.environ.get('AGENTRY_LITELLM_API_KEY'); print('chave:', 'presente' if v else 'ausente')"
```

Não confira com `grep "$CHAVE"` nem `echo`: o próprio comando de checagem põe a chave em
argv, visível em `ps`.

## Rota 1 — `oa-chat`: chamada direta, modo texto

O conteúdo vai embutido no pedido. Determinístico, não depende de o modelo saber usar
ferramentas. É a rota padrão para revisar diff, resumir documento, classificar lista,
extrair campos.

```bash
OA=skills/delegacao-openai-compat/scripts/oa-chat
$OA --models                                    # o que o endpoint serve
$OA -m <modelo> --no-think -f pedido.md > resposta.md 2> uso.txt
git diff --staged | $OA -m <modelo> --no-think -s "Voce e revisor." - > revisao.md 2> uso.txt
$OA -m <modelo> --no-think --json -f extrair.md > saida.json 2> uso.txt
```

O script garante o que é fácil esquecer: chave e corpo **fora de argv**; URL normalizada;
resposta não-JSON e erro HTTP viram mensagem legível; uso de tokens em `stderr`
(`[uso] modelo=… entrada=… saida=… fim=…`).

| Código | Significado |
|---|---|
| `0` | Resposta completa |
| `1` | Erro do endpoint ou de conexão |
| `2` | Uso ou configuração |
| `3` | Resposta vazia ou truncada (`finish_reason=length`) |

### Modelos de raciocínio: o gasto invisível

Modelos de raciocínio consomem `max_tokens` **pensando antes de responder**. Com orçamento
curto, a resposta vem **vazia** com `finish_reason=length` — e um script ingênuo imprime
`null` como se fosse resultado. O `oa-chat` sai com código `3` nesse caso.

Medido num GLM servido por vLLM atrás de LiteLLM, pedindo um parágrafo de 150 palavras:

| Configuração | Tokens de saída | Resultado |
|---|---|---|
| Padrão, `max_tokens=3000` | 3000 | **Vazio** — tudo gasto raciocinando |
| `reasoning_effort=low` | 3000 | **Vazio** — parâmetro ignorado em silêncio |
| `--no-think` | ~230 | Parágrafo completo |

Para trabalho mecânico — extração, classificação, formatação — **use `--no-think`**. A
economia é de uma ordem de grandeza. Reserve o raciocínio para quando a tarefa exige
inferência e a verificação barata não basta.

### Desligar o raciocínio: a chave depende da implantação

Não existe chave padrão. Cada servidor obedece a uma, e o **mesmo modelo** responde diferente
conforme quem o serve. O `--no-think` manda as duas conhecidas:

| Chave | Quem obedece |
|---|---|
| `chat_template_kwargs.enable_thinking=false` | vLLM/SGLang, pelo template de chat do modelo |
| `thinking: {"type": "disabled"}` | API no formato Anthropic/Z.ai, e proxies que a repassam ao servidor |

Endpoint que **recusa** uma delas — o LiteLLM responde `400 UnsupportedParamsError` para
`thinking` em modelo que não a declara, como os servidos por Ollama — recebe a chamada de novo
sem a chave recusada, com aviso em stderr. Chave pedida em `--extra` nunca é retirada: ali a
recusa é erro de verdade.

Medido em 2026-10-29, mesmo gateway LiteLLM, pedido trivial ("responda OK"), 3 chamadas por
configuração (`--sonda-think`):

| Modelo | `template` | `thinking` | `--no-think` (as duas) |
|---|---|---|---|
| GLM-5.2 (vLLM) | **desliga** (2 tokens) | ignorado (139) | **desliga** |
| GLM-5.3 | **vaza** | ignorado (88) | **vaza** |
| qwen3-coder (Ollama) | desliga | **recusado (400)** | desliga, pelo recuo |

**GLM-5.3 é o caso a conhecer.** Em uso real atrás de LiteLLM, o `--no-think` antigo (só
`template`) estourava `max_tokens` raciocinando, e `thinking: {"type": "disabled"}` resolveu —
foi por isso que a chave entrou no `--no-think`. Na medição acima, nenhuma das duas desligou,
e a de template fez pior: o raciocínio **vazou para o conteúdo** ("The user is asking…") com
código 0. A diferença entre os dois resultados é a razão da sonda: o que vale num endpoint não
se transfere para outro. É o pior modo de falha, porque passa por resposta. Desconfie de
resposta em outra língua, ou que começa descrevendo o pedido.

Por isso, **antes de confiar no `--no-think` num endpoint e modelo novos, sonde uma vez:**

```bash
$OA --sonda-think -m <modelo>
```

A sonda faz 12 chamadas triviais e classifica cada uma como **desligou**, **pensou**
(respondeu certo, mas raciocinando), **vazou** (código 0 com outra coisa no lugar da resposta),
**estourou** ou **recusou**. No fim diz qual chave usar, ou que nenhuma serve. Se nenhuma serve,
dimensione `--max-tokens` e divida o pedido por item (seção seguinte).

### O orçamento de raciocínio escala com o tamanho da TAREFA, não da resposta

Aumentar `--max-tokens` não resolve pedido grande: o raciocínio cresce com o número de
decisões pedidas. Medido no mesmo modelo, com o mesmo acervo, no mesmo dia:

| Pedido | `--max-tokens` | Saída | Resultado |
|---|---|---|---|
| 8 a 15 skills, 9 campos cada, numa chamada | 32.000 | 32.000 | **Vazio** nas 4 tentativas |
| 1 skill, os mesmos 9 campos | 20.000 | ~6.000 | Completo, com citação por item |

Quatro lotes grandes gastaram ~131 mil tokens e devolveram **nada**; 38 pedidos pequenos
devolveram 38 respostas. **Divida por item, não por tema**, e sonde com uma chamada antes de
abrir o leque — a sonda custa uma chamada e evita refazer o lote inteiro.

### Lote: o harness só observa o processo que ele iniciou

Ao disparar várias chamadas, **não use `nohup` nem `&` na chamada que o agente faz**. O
invólucro sai em segundos, é reportado como concluído — corretamente — e o trabalho destacado
termina **sem aviso nenhum**. Aconteceu: 21 chamadas ficaram prontas às 16:44 e só foram
notadas às 19:29.

- O trabalho longo roda em **primeiro plano dentro** da chamada em segundo plano. Aí o fim da
  notificação coincide com o fim do trabalho.
- Se o destacamento for inevitável, a chamada seguinte é um **laço de espera** cuja saída
  coincide com o término — testando arquivo de estado, nunca `sleep` fixo seguido de `echo`.
- Antes de dizer "ainda rodando", verifique o **processo**: `pgrep -x <binário>`, nunca
  `pgrep -f`, que casa com a própria linha de comando e sempre acha a si mesma. E o `mtime` do
  arquivo de estado, que diz quando o trabalho de fato parou.

### Respostas de modelo são material a conferir, não resultado

Toda afirmação do modelo sobre o conteúdo de um arquivo é hipótese até você abrir o arquivo.
Medido na mesma rodada: um modelo deu veredito oposto ao próprio argumento (recomendou
substituir o nosso e usou três linhas para mostrar que o nosso era melhor); outro contou "três
regras" onde o original diz *"two rules"*; e um terceiro declarou lacuna que não existia porque
**o pedido só lhe deu três dos itens do acervo**. O último é defeito do pedido, não do modelo:
pergunta cuja evidência não foi entregue não pode ser respondida, e vem respondida.

## Rota 2 — `agentry`: modo agente

Para varredura ampla, onde o modelo precisa ler arquivos sozinho. Depende de tool-calling
decente **e** das `permissions` do perfil — sob `externo-confidencial`, `readAllow` é lista
fechada, então **diga o caminho exato**.

O `agentry` fala com o endpoint pelo adapter OpenAI-compatible, configurado no bloco
`providers.litellm` do `.agentry/agentry.settings.json` — o nome do bloco é do schema do
`agentry`, e serve a qualquer endpoint compatível. O template anexo traz o bloco e a
task-class `delegada`:

```bash
jq -s '.[0] * .[1]' .agentry/agentry.settings.json \
   skills/delegacao-openai-compat/templates/agentry-litellm.snippet.json > /tmp/settings.novo
diff -u .agentry/agentry.settings.json /tmp/settings.novo   # revise antes de mover

bash skills/delegacao-openai-compat/scripts/com-chave-litellm.sh --check
bash skills/delegacao-openai-compat/scripts/com-chave-litellm.sh \
  agentry --task-class delegada 'Leia docs/x.md com fs_read. Responda SOMENTE ...'
```

Três armadilhas silenciosas do `agentry`: sem `baseUrl` **e** `model`, o provider não é
registrado; sem `egressClass`, o candidato nunca resolve sob perfil restritivo e a chamada
cai no Ollama sem erro; variável `AGENTRY_LITELLM_API_KEY` **definida e vazia** vence o
`credentials.json` e o gateway responde `401`.

## O pedido: autocontido ou inútil

O endpoint não vê esta conversa. Os quatro elementos da `delegacao-a-subagentes` valem —
tarefa concreta, formato exato da resposta, proibição campo a campo, sentinela de falha —
com três agravantes:

1. **Contexto zero.** Todo caminho, nome e critério vai no pedido.
2. **Você paga por token de entrada.** O arquivo certo, não a pasta; o diff, não o histórico.
3. **O modelo é desconhecido.** Peça o formato mais simples que resolva, e prefira lotes
   pequenos: dez itens por chamada erram menos que cem.

## O padrão que não enche o contexto

1. **`stdout` para arquivo.** Nunca deixe a resposta inteira voltar para a conversa.
2. **Leia um recorte.** `jq`, `grep`, contagem — o arquivo inteiro só se preciso.
3. **`stderr` para `uso.txt`.** O custo fica registrado sem sujar a resposta.

## O que delegar — e o que não

| Delegue | Não delegue |
|---|---|
| Extração estruturada a partir de entrada volumosa | Decisão de arquitetura, trade-off, escolha de dependência |
| Primeira passada de revisão de diff | O que custa mais verificar do que fazer |
| Resumo de log, transcrição, documento longo | Escrita direta em arquivo do projeto sem revisão |
| Normalização e tradução de formato em lote | Material sob NDA para endpoint sem egresso declarado |
| Rascunho de proposta que você vai revisar | Tarefa encadeada de muitos passos |

## O que você vai pensar para pular a verificação

| O que você vai pensar | Por que não vale |
|---|---|
| "O formato veio certo, o conteúdo deve estar" | Formato certo é pré-condição, não evidência. Amostre. |
| "São 135 itens, conferir três não prova nada" | Prova o suficiente para **descartar** o lote. Um erro na amostra derruba tudo. |
| "É o modelo grande do gateway, é confiável" | Você não mediu. E `--no-think` muda o comportamento dele. |
| "Passei `--no-think`, então ele não raciocina" | Depende de quem serve o modelo. Já se mediu `--no-think` ignorado e vazando o raciocínio para o conteúdo com código 0. `--sonda-think` uma vez por endpoint e modelo. |
| "Veio `SEM_ACHADOS`, então não há achados" | Pode ser `401`, candidato indisponível ou pedido mal entendido. Sentinela inesperada é falha de rota. |
| "Refazer aqui custaria a cota que eu queria poupar" | Usar resultado errado custa mais que a cota. |

## Verificação obrigatória

- **Formato primeiro.** Resposta fora do formato pedido ⇒ o modelo não entendeu; o conteúdo
  provavelmente também está errado.
- **Amostre na fonte.** Dois ou três itens conferidos contra o original; um errado derruba o
  lote.
- **Código `3` não é resultado.** Resposta vazia ou truncada volta com mais `--max-tokens` ou
  `--no-think` — nunca entra como dado.
- **Registre o custo** (`uso.txt`) quando estiver comparando rotas.

## Endpoint local não é local se houver proxy no ambiente

`HTTP_PROXY`, `HTTPS_PROXY` e `ALL_PROXY` no ambiente valem também para `127.0.0.1`. Com um
deles definido, a chamada que você acha que fica na máquina **sai para um terceiro** — e o
registro continua dizendo "local", porque o que se anotou foi o host da URL, não o destino
real da conexão.

Medido: com `ALL_PROXY` apontando para uma porta fechada, `curl http://127.0.0.1:8765/`
devolve 000; com `--noproxy '*'`, devolve 200. A diferença entre vazar e não vazar é uma
opção de linha de comando.

O `oa-chat` já passa `--noproxy '*'` quando o endpoint é loopback ou rede privada
(`127.*`, `::1`, `10.*`, `192.168.*`, `172.16-31.*`) — e é o **único** caminho daqui em que
isso está verificado. Cliente HTTP que adota proxy do ambiente por padrão (o caso comum em
várias bibliotecas) não tem essa proteção, e o modo agente de outro programa é um deles até
que se prove o contrário. Em qualquer ferramenta que não seja o `oa-chat`, confira antes:

```bash
env | grep -iE '^(http|https|all)_proxy=' || echo 'sem proxy no ambiente'
```

**Desligar proxy é metade.** A outra metade é **validar o destino resolvido**, não o texto do
host: um nome que parece local e resolve para fora passa por qualquer checagem feita sobre a
URL. Não conheço implementação aqui nem no runtime vizinho que faça as duas hoje — então, com
material sensível, a garantia atual é "proxy desligado", e não "não sai da máquina".

> **Classe de egresso descreve fronteira de confiança, não distância de rede.** Um gateway
> interno remoto pode ser mais confiável que um proxy local desconhecido — e é por isso que a
> classe se declara por endpoint, em vez de deduzir do IP.

## Definição de pronto da skill

- [ ] O egresso do endpoint era conhecido **antes** do envio, e compatível com o material.
- [ ] Endereço, chave e modelo vieram do ambiente — nada escrito no repositório.
- [ ] A chave nunca apareceu em argv, em saída nem em comando de checagem.
- [ ] O pedido era autocontido: caminhos, formato, proibições, sentinela.
- [ ] A saída foi para arquivo; só um recorte entrou no contexto.
- [ ] Nenhuma resposta com código `3` foi usada como resultado.
- [ ] O resultado foi amostrado na fonte antes de ser usado.

- [ ] Nenhum proxy do ambiente intercepta endpoint declarado `local-only`.
