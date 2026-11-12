---
name: checagem-fatos
invocacao: modelo
description: >-
  Verifica conteúdo suspeito ou alarmista (vídeo, áudio, print, texto de
  WhatsApp, post de Facebook, Instagram ou TikTok, link de notícia) pelo método
  das agências de checagem: extrai as
  alegações checáveis, busca primeiro em fonte oficial, classifica cada uma numa
  escala fixa e entrega relatório com a informação correta e as referências
  marcadas como oficiais ou não oficiais, mais um resumo pronto para responder a
  quem mandou. Aciona quando pedirem para "checar", "verificar", "isso é
  verdade?", "é fake?", ou ao receber link ou mensagem com tom de alerta.
---

# checagem-fatos — a alegação contra a fonte oficial, uma por uma

Conteúdo alarmista raramente é mentira pura. O padrão mais comum é **fatos reais
costurados a uma conclusão que eles não sustentam**: um teste de alerta real, um decreto real,
um episódio de desenho real — e a conclusão "vai haver apagão mundial". Por isso a checagem
não julga o conteúdo inteiro de uma vez: **separa as alegações e confere cada uma**, e o
veredito geral sai da soma.

O método segue o que as agências de checagem fazem — o Código de Princípios da IFCN
(apartidarismo, transparência de fontes e de método, política de correção) e as práticas de
Lupa, Aos Fatos, Comprova e AFP Checamos — com a leitura lateral do método SIFT.

## O princípio

> Fonte oficial primeiro. Sem fonte oficial, a fonte que houver — **dita como não oficial**.
> Nenhuma alegação sem referência, nenhuma referência sem etiqueta.

## Procedimento

### 1. Preservar o conteúdo antes de qualquer coisa

Conteúdo alarmista é apagado ou editado depois que viraliza. Registre o link, a data de
publicação, o autor/canal e guarde o material:

| Origem | Como obter o conteúdo | O que guardar |
|---|---|---|
| **YouTube** | legenda da plataforma — `transcrever-video/scripts/legendas.py` | `.txt` + `.meta` |
| **Facebook, Instagram, TikTok, Kwai, X** (vídeo/Reels) | quase nunca há legenda: `transcrever-video/scripts/asr-local.py <url>` (baixa só o áudio, Whisper local) | `.txt` com origem ASR declarada + `.meta` (autor, data, legenda do post) |
| Post de rede social **que exige login** | o usuário baixa o arquivo ou tira print e passa o caminho; ou leitura pelo navegador da própria pessoa (Claude in Chrome), só de leitura | arquivo/print + URL |
| **Texto do post** (legenda, descrição) | vem no `.meta` (`title`) via yt-dlp; senão, print | idem |
| **Áudio de WhatsApp/Telegram** | exportar o `.opus`/`.ogg` e rodar `asr-local.py <arquivo>` — **nunca** serviço externo | `.txt` |
| **Print / imagem** | transcreva o texto; busca reversa (Google Lens, TinEye, Yandex) para achar origem e data reais | print |
| **Texto encaminhado** (corrente) | busque um trecho exato entre aspas — corrente costuma ter anos e várias versões | o texto |
| **Notícia / site / blog** | leitura direta; salve no Web Archive (`web.archive.org/save/<url>`) | URL arquivada + data da matéria |
| **PDF** (relatório, "documento vazado") | `dominio/docling-local`; confira se o documento existe no site do emissor | PDF + `.md` |

Os scripts são da skill [`dominio/transcrever-video`](../transcrever-video/SKILL.md). Copie a
transcrição para junto do relatório — o post pode sumir.

**Não registre** nome, telefone ou dado pessoal de quem enviou. O relatório trata do conteúdo.

#### Acesso às redes sociais: por que não há chave de API

Nenhuma das três oferece API de leitura de posts públicos para uso pessoal:

- **Meta (Facebook/Instagram)** — a Graph API só lê páginas e contas que você administra. O
  acesso a conteúdo público de terceiros é a **Meta Content Library**, restrita a pesquisadores
  de instituições sem fins lucrativos, com candidatura revisada.
- **TikTok** — a Research API é para pesquisadores acadêmicos e organizações sem fins
  lucrativos aprovados; a API de exibição só mostra o conteúdo da própria conta.

O caminho prático é o mesmo de um checador sem convênio: **yt-dlp para vídeo público**,
**arquivo ou print enviado pela pessoa** quando há login, e **o navegador da própria pessoa**
quando é preciso ler a página. Não use `--cookies-from-browser`: entrega a sessão inteira ao
script, e conta usada por automação pode ser bloqueada.

### 2. Avaliar a fonte (leitura lateral)

Antes de ler a fundo o que o conteúdo diz, saia dele e pergunte **sobre** ele (o "I" e o "F"
do SIFT):

- **Quem publica?** Veículo com redação e expediente, órgão público, canal pessoal, perfil
  anônimo? O que outras fontes dizem sobre ele?
- **Quando?** Data original *versus* repostagem — boato velho com data nova é o caso mais
  frequente.
- **Quem ganha?** Monetização por clique, patrocínio, venda de produto (kits de sobrevivência,
  suplemento, curso). Título alarmista com conteúdo moderado é *clickbait*: registre, mas
  julgue as alegações, não o título.

Em **rede social**, além disso:

- **Cadeia de repostagem.** "Reprodução: @perfil", marca d'água de outro app, corte de live:
  ache o **post original** e a data dele — o repost muda contexto e data sem avisar.
- **Conta.** Idade da conta, troca de nome, verificação, outros posts do mesmo tom. Selo de
  verificado prova identidade, não veracidade.
- **Engajamento não é evidência.** "99 mil visualizações" mede alcance, não verdade.
- **Mídia reciclada ou sintética.** Imagem/vídeo de outro evento ou de anos antes (busca
  reversa por quadro-chave — extensão InVID-WeVerify); voz ou rosto gerado por IA (lábio fora
  de sincronia, voz sem respiração, mãos e texto deformados). Suspeita sem prova vira ❔, não ❌.
- **Rótulo da plataforma.** Aviso de checagem, Nota da Comunidade (X) ou "informação falsa"
  (Meta) entram como `[N]`, com o link do checador que o originou.
- **Narrativa costurada.** O formato mais comum em vídeo de opinião: uma sequência de
  notícias verdadeiras ("vamos aos fatos") seguida de uma conclusão que nenhuma delas sustenta.
  Cheque as notícias uma a uma, e trate a **ligação entre elas** como alegação própria — é ali
  que costuma estar o 🟠.

### 3. Extrair as alegações checáveis

Checável é o que pode ser confrontado com um registro: **número, data, evento, citação
atribuída, nome de lei/órgão/programa, relação causal afirmada**. Anote o momento (`mm:ss`)
ou o trecho.

- Não checável — opinião, previsão, especulação ("dá para imaginar que…") — entra na tabela
  como 💬 **Opinião**, para mostrar que foi vista, sem veredito de verdade.
- **Priorize**: primeiro a tese central (a do título), depois o que pode causar dano se for
  acreditado (saúde, dinheiro, segurança, "estoque comida"), depois o resto.
- Não reescreva a alegação para facilitar: cite-a como foi dita, resumida sem mudar o sentido.

### 4. Buscar a fonte — nesta ordem

| Nível | Etiqueta | Exemplos |
|---|---|---|
| **Oficial** | `[O]` | Diário Oficial, texto da lei ou decreto, site `.gov`/`.gov.br`, órgão regulador, tribunal, banco central, instituto estatístico (IBGE), organismo internacional (OMS, ONU), comunicado oficial **da própria organização** de quem se fala, artigo científico revisado por pares (a fonte primária, não a notícia sobre ele) |
| **Não oficial — checador** | `[N]` | Signatários da IFCN: Lupa, Aos Fatos, Comprova, AFP Checamos, Estadão Verifica, Fato ou Fake (g1), UOL Confere; Reuters/AP Fact Check |
| **Não oficial — imprensa** | `[N]` | Veículo profissional com expediente e política de correção; agência de notícias |
| **Não oficial — outros** | `[N]` | Blog, rede social, fórum, vídeo — só como "onde a informação circula", nunca como prova |

Regras:

- **Vá ao documento, não à notícia sobre o documento.** Se a matéria cita um decreto, abra o
  decreto. A notícia entra como `[N]` complementar, se ajudar.
- **Sem fonte oficial localizada**, mostre as fontes que trazem a informação, todas `[N]`, e
  escreva **"Sem fonte oficial localizada"** na célula da informação correta. O veredito fica
  limitado pelo que essas fontes permitem afirmar.
- Ausência de registro oficial sobre algo que **deveria** ter registro (uma lei, um decreto, um
  comunicado de órgão) é evidência — "não existe decreto com esse número" é verificável.
- Fonte que concorda com o boato não é confirmação se ela própria não tem fonte.
- Anote a data da consulta: alegação sobre evento futuro ou em andamento expira.

### 5. Classificar

Escala fixa, adaptada das usadas por Lupa e Aos Fatos:

| Selo | Classificação | Quando |
|---|---|---|
| ✅ | **Verdadeiro** | Confere com a fonte |
| 🟡 | **Impreciso** | Essencialmente correto, com erro de detalhe (número, data, nome, local) que não muda a conclusão |
| 🟠 | **Distorcido** | Parte de fato real, mas exagera, tira de contexto ou tira conclusão que o fato não sustenta |
| ❌ | **Falso** | A fonte contradiz |
| ❔ | **Insustentável** | Não há evidência pública que confirme nem desminta |
| 💬 | **Opinião** | Não é alegação de fato; registrada sem veredito |

Classifique **a alegação, nunca a pessoa**: nada de "mentiroso", "golpista", "desinformador".
Mesma régua para qualquer lado político — o critério é a fonte, não a simpatia.

### 6. Escrever o relatório

Use o modelo em [`templates/relatorio.md`](templates/relatorio.md). A tabela tem **cinco
colunas, nesta ordem**:

| # | Alegação (tempo/trecho) | Classificação | Informação correta | Referências |
|---|---|---|---|---|

- **Informação correta** — o que a fonte diz, em uma ou duas frases, com o número/data exatos.
  Em ✅, confirme o dado; em ❌/🟠/🟡, corrija; em ❔, diga o que se sabe e o que falta.
- **Referências** — links etiquetados, `[O] [Título](url)` ou `[N] [Título](url)`, separados
  por `<br>`. Em 💬, pode ser `—`.

Acima da tabela, o **veredito geral** em uma frase (o conteúdo, como um todo, informa ou
engana?). Abaixo, as **ressalvas sobre o conteúdo** (título, monetização, mistura de opinião
com fato).

### 7. O que dizer a quem mandou

Quatro a seis frases, linguagem de conversa, prontas para colar no WhatsApp. Técnica do
**sanduíche da verdade**: comece pelo fato, mencione o boato uma vez, sem repetir a frase de
efeito, e termine no fato e no que fazer (ou não fazer). Sem ironia e sem tom de
correção — quem encaminhou estava preocupado, não mal-intencionado.

### 8. Validar e registrar

```bash
python3 skills/dominio/checagem-fatos/scripts/checar-relatorio.py <relatorio.md>
```

Reprova linha sem referência, referência sem etiqueta `[O]`/`[N]`, classificação fora da
escala e linha só com `[N]` que não declare "Sem fonte oficial localizada". O
`--autoteste` prova as regras sem rede.

Relatório em `verificacoes/AAAA-MM-DD_<tema>.md`; transcrição ou print preservado ao lado.
**Correção**: se um fato mudar depois (decreto revogado, evento adiado), edite o relatório e
acrescente uma linha `Corrigido em AAAA-MM-DD: <o quê>` — não apague o histórico.

## Limites

- A checagem diz **o que as fontes registram**, não dá conselho médico, jurídico ou
  financeiro. Em saúde, aponte o órgão (Ministério da Saúde, Anvisa, OMS); em risco imediato,
  a Defesa Civil.
- Legenda automática erra nome próprio e número: confira no vídeo antes de classificar uma
  alegação como 🟡 por causa de um detalhe.
- Fato em andamento (evento marcado para amanhã) se checa contra o que foi **anunciado**, e o
  relatório diz isso.

## Ligação com o resto do acervo

`dominio/transcrever-video` obtém o texto de vídeos; `dominio/docling-local` lê o PDF de uma
lei ou relatório oficial sem corromper números. `critico-independente` serve quando o
assunto for sensível o bastante para pedir uma segunda leitura em contexto limpo.

## Definição de pronto

- [ ] Conteúdo preservado (transcrição, print ou arquivo do Web Archive) e data anotada.
- [ ] Toda alegação checável na tabela, com momento ou trecho; opiniões marcadas 💬.
- [ ] Toda linha com **Informação correta** e **Referências** etiquetadas `[O]`/`[N]`.
- [ ] Linha sem `[O]` declara "Sem fonte oficial localizada".
- [ ] `checar-relatorio.py` passou.
- [ ] Resumo para quem mandou, sem dado pessoal de ninguém.
