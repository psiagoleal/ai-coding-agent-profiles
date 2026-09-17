<!-- Caminho relativo: docs/adr/0010-delegacao-a-gateway-litellm.md -->

# ADR 0010: Delegação de volume a gateway LiteLLM como rota distinta da delegação local

- **Status:** Accepted
- **Data:** 2026-09-09
- **Decisores:** Iago Leal (mantenedor)
- **Tags:** interop, agentry, skills, delegação, confidencialidade, custo

> **Atualização (2026-09-17).** A skill decorrente desta decisão foi renomeada de `delegacao-litellm` para `delegacao-openai-compat` e generalizada para qualquer endpoint OpenAI-compatible, com o script `oa-chat` para chamada direta. A decisão abaixo continua valendo; só o alcance da skill cresceu.

## Contexto

A ADR-0007 distribuiu a arquitetura de delegação "nuvem planeja, local lê": o agente
principal decide, o subagente local (Ollama) toca o que é sensível. Ela resolve
**confidencialidade** — nada sensível sai da máquina — e a skill `delegacao-a-subagentes`
documenta a fronteira.

Restou sem resposta um problema **econômico**, hoje o gargalo prático do trabalho diário:

- A cota da assinatura (janelas de 5h/7d, ver skill `limites-de-uso`) é o recurso escasso, e
  ela é consumida igualmente por trabalho de julgamento e por trabalho de volume mecânico —
  varrer arquivos, resumir log, primeira passada de revisão.
- **Subagente do agente principal não resolve isso.** Ele isola *contexto*, não *consumo*:
  roda no mesmo provedor da sessão e debita a mesma cota. A confusão entre as duas coisas é
  frequente o bastante para exigir registro.
- O modelo local resolve o consumo, mas não substitui um modelo capaz em tarefa de volume com
  formato exigente — e a skill irmã já documenta que encadeamento longo degrada rápido ali.

O `agentry` já tem, desde a v0.1, a peça que falta: `providers.litellm` (ADR-0006 daquele
repo), consumido pelo adapter OpenAI-compatible, com `taskClasses` roteando por classe de
egresso e `--set-credential` gravando a chave fora de qualquer arquivo versionado (ADR-0038).
Nada disso estava exposto como **prática** na biblioteca de skills: o operador tinha as peças
e nenhuma orientação sobre quando usá-las, o que a rota não garante, e como não vazar material
sob NDA por um proxy cujo host é local mas cujo destino é a nuvem pública.

## Decisão

Fica acordada a criação da skill de governança **`delegacao-litellm`**, irmã (não substituta)
de `delegacao-a-subagentes`, estabelecendo o gateway LiteLLM como **terceira rota** de
delegação, escolhida por critério explícito:

| Necessidade dominante | Rota | Cota | Contexto |
|---|---|---|---|
| Julgamento (arquitetura, decisão, código não trivial) | agente principal / seu subagente | gasta | isola |
| Confidencialidade (o dado não pode sair da máquina) | subagente local — ADR-0007 | poupa | isola |
| Volume verificável sobre material liberado | `agentry` → `litellm` — **esta ADR** | poupa | isola |

Três compromissos acompanham a decisão:

1. **A checagem de egresso é pré-condição, não recomendação.** A skill reproduz o
   *fail-closed invertido* da ADR-0006 do `agentry` — gateway sem `egressClass` declarada é
   tratado como `cloud-ok`, logo proibido para material sob NDA — e exige as três perguntas
   (para onde roteia, há opt-out nos backends, quem operou declarou a classe) **antes** do
   primeiro envio. Host local não é evidência de destino local.
2. **A chave nunca transita por argumento, arquivo versionado ou terminal.** A skill traz um
   script anexo (`scripts/com-chave-litellm.sh`, sob a ADR-0004) que resolve a chave de uma
   cadeia de fontes — ambiente, comando de cofre, arquivo JSON com expressão `jq`, arquivo de
   uma linha — e a exporta **apenas para o processo filho**; recusa placeholder não
   substituído e recusa rodar sob `set -x`. Quando a chave já está em
   `~/.agentry/credentials.json`, o script não abre o arquivo: deixa o `agentry` resolver.
3. **A skill fixa o padrão de invocação que preserva contexto** — `stdout` para arquivo,
   leitura por recorte, `stderr` guardado para a linha `[uso]` — porque delegar e depois
   colar a resposta inteira na conversa desfaz metade do ganho.

Distribuição segue a ADR-0006 deste repositório (**valores, nunca schema**): a skill traz um
`templates/agentry-litellm.snippet.json` para o operador mesclar no seu
`.agentry/agentry.settings.json`, com `baseUrl`/`model`/`egressClass` como placeholders
explícitos. **Os perfis não passam a distribuir um bloco `providers.litellm` preenchido:** o
endpoint e, sobretudo, a classe de egresso são fatos do gateway de cada operador, e um valor
default aqui seria exatamente a inferência que a ADR-0006 do `agentry` proíbe.

## Consequências

- **Impacto positivo:** trabalho de volume deixa de consumir a cota escassa, com a fronteira
  de confidencialidade explicitada em vez de presumida; zero código novo no `agentry` — a
  skill só expõe capacidade já existente e testada.
- **Impacto positivo:** a distinção "isola contexto ≠ isola consumo" passa a estar escrita, em
  vez de ser redescoberta a cada sessão.
- **Impacto negativo:** mais uma rota para o operador escolher errado; mitigado pela tabela de
  decisão e pelas listas de "o que delegar / o que não" da skill.
- **Impacto negativo:** a garantia de confidencialidade da rota depende de uma declaração
  humana sobre o gateway. O framework audita a fronteira; não audita o interior do proxy —
  mesma limitação já assumida na ADR-0006 do `agentry`, agora herdada aqui.
- **Trade-offs aceitos:** custo financeiro por token no gateway em troca de cota de
  assinatura; menor fidelidade a recursos nativos de provedor (ex.: *prompt caching*) quando o
  acesso é intermediado pela superfície OpenAI.

## Diretriz de Conformidade de Código

- **Proibido:** enviar material sob NDA a um gateway sem `egressClass` declarada por quem o
  opera; inferir classe de egresso a partir do host (`localhost` ⇒ `local-only`); embutir a
  chave de API em `agentry.settings.json`, em `config.toml`, em argumento de linha de comando
  ou em qualquer arquivo versionado; ecoar a chave em terminal ou log; distribuir nos perfis um
  `providers.litellm` com endpoint ou classe de egresso preenchidos.
- **Obrigatório:** todo acesso ao gateway passa pelo `agentry` (adapter OpenAI-compatible), com
  a chave resolvida via variável de ambiente, cofre ou `~/.agentry/credentials.json`; a
  delegação é sempre um pedido autocontido com formato de resposta e sentinela de falha
  declarados; o resultado é verificado por amostragem antes de ser usado; a saída vai para
  arquivo e só o recorte necessário entra no contexto da sessão.

> Qualquer desvio desta regra viola as diretrizes de conformidade arquitetural do projeto
> e deve ser reportado para revisão antes de prosseguir.
