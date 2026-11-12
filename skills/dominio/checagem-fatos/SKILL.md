---
name: checagem-fatos
invocacao: modelo
description: >-
  Verifica conteúdo suspeito ou alarmista (vídeo, áudio, print, texto de
  WhatsApp, link de notícia) pelo método das agências de checagem: extrai as
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

| Formato | Como obter o texto |
|---|---|
| Vídeo (YouTube etc.) | skill [`dominio/transcrever-video`](../transcrever-video/SKILL.md); copie a transcrição para junto do relatório |
| Áudio de WhatsApp | ASR **local** (ver `transcrever-video`, caminho caro) — áudio de família não vai para serviço externo |
| Print / imagem | transcreva o texto; faça busca reversa da imagem (Google Lens, TinEye) para achar a origem e a data reais |
| Texto encaminhado | busque um trecho exato entre aspas — corrente costuma ter anos e várias versões |
| Notícia / site | salve no Web Archive (`web.archive.org/save/<url>`) e anote a data da matéria |

**Não registre** nome, telefone ou dado pessoal de quem enviou. O relatório trata do conteúdo.

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
