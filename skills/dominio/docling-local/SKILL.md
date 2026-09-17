---
name: docling-local
description: >-
  Converte PDFs (normas técnicas, artigos, manuais, relatórios) em Markdown
  utilizável pelo serviço docling local, preservando índices, expoentes, letras
  gregas e equações em LaTeX — que `pdftotext` corrompe — e grava o resultado na
  base de referências do projeto com procedência declarada. Aciona ao pedir para
  extrair/converter/ler um PDF, ao citar uma norma ou artigo que só existe em
  PDF, ao montar ou alimentar uma base de conhecimento documental, ou quando a
  extração precisar de equações, tabelas ou figuras confiáveis.
---

# docling-local — PDF em Markdown com procedência

## Por que não `pdftotext`

`pdftotext` é rápido, está em toda máquina e resolve texto corrido. Mas ele
**perde radicais, índices, expoentes e letras gregas**. Numa norma técnica isso é
fatal: `q₀` sai como `q 0`, `G_c` como `G c`, `sin²Ω` como `sin 2 Ω`, e uma raiz
quadrada simplesmente desaparece — restando uma fração que parece correta e não é.
O agente então cita uma equação errada com toda a confiança do mundo.

O docling entrega a mesma equação como LaTeX:

```
$$A _ { \text{c} } = q _ { 0 } \ C _ { \text{x} } \ G _ { \text{c} } \ G _ { \text{L} } \, d \, L \, \sin ^ { 2 } \, \Omega$$
```

Custa alguns minutos de conversão. Numa norma que vai ser citada em relatório,
contribuição técnica ou parecer, é o melhor negócio da tarefa.

## Princípio central (restrição cognitiva)

**Extração é fonte, não resposta.** Um `.md` de 90 mil palavras não é
conhecimento: é matéria-prima cujas perdas você ainda não conhece. Toda extração
carrega três dívidas, e todas se declaram no cabeçalho do arquivo:

1. **O que se perdeu** — figuras, páginas com erro de stream, trechos ilegíveis.
2. **O que não foi conferido** — o que você não leu não está verificado, por mais
   bonito que o Markdown esteja.
3. **De onde veio** — arquivo de origem, data, ferramenta, e **licença**. Norma
   técnica costuma trazer carimbo nominal de licenciado; remover o carimbo do
   texto é higiene, apagar a procedência é outra coisa.

Daí a regra de dois arquivos: a extração integral, e ao lado uma **transcrição
conferida** do que de fato importa. Nunca cite direto da extração integral um
número que você não conferiu contra a imagem da página.

## Conferir barato — a ordem importa

A conversão pelo docling é barata: minutos de GPU, quase nada de janela de
contexto. **O caro é a conferência**, e por um motivo que não é óbvio:

> **Toda imagem lida permanece no contexto e é reenviada em cada requisição
> seguinte.** Ler 60 páginas não custa 60 leituras — custa 60 leituras mais o
> arrasto de 60 imagens em todas as trocas até a próxima compactação.

Medido na NBR 5422:2024 (124 páginas escaneadas): a conversão levou ~8 min de
GPU; a conferência de ~60 páginas consumiu a janela inteira duas vezes.

**Siga esta ordem. Só desça um degrau quando o anterior não resolver.**

### 1º — Recalcular, quando o dado tem estrutura

Grátis, e é **evidência mais forte que ler**. Se a tabela ou a fórmula tem
estrutura matemática, ela se verifica sozinha:

| O que checar | Como |
|---|---|
| Função definida por partes | Os ramos batem na fronteira? |
| Tabela derivada de fórmula | Recalcule a fórmula e compare linha a linha |
| Coluna que é razão de outras duas | Divida e confira |
| Valores lidos de figura | A forma fechada reproduz os pontos do gráfico? |
| Constantes assintóticas | Batem com a teoria? |

Na NBR 5422:2024 isso pegou o que a leitura **não** teria pego: as colunas
`T`=2 e `T`=10 da Tabela A.2 deslocadas em uma linha, descoberto ao recalcular
`K_T,n = (C_T − C₂)/C₁` — que depois se revelou ser a fórmula A.2.5 da própria
norma. Também validou os dois ramos de `G₀` pela continuidade, as emendas do
polinômio de `G_L` em 200 e 800 m, e as oito linhas de `C₁`/`C₂` na quinta
decimal. Custo: alguns segundos de `python3 -c`.

⚠️ Recálculo confirma **consistência**, não leitura. Se o recálculo diverge, o
próximo passo é o recorte — pode ser erro seu de leitura, e não da norma.

### 2º — Recortar a região, não ler a página

`pdftoppm` aceita janela de recorte. Uma tabela ocupa um terço de uma A4; ler a
página inteira custa o triplo à toa. E o recorte permite **DPI alto** onde
importa, que é o que decide dígito duvidoso:

```bash
# página inteira, referência rápida
pdftoppm -r 140 -f 39 -l 39 -png "doc.pdf" saida/p

# só a tabela, em 300 dpi: -x/-y canto superior esquerdo, -W/-H tamanho
pdftoppm -r 300 -x 500 -y 2830 -W 2000 -H 260 -f 110 -l 110 -png "doc.pdf" saida/zoom
```

Na NBR, foram dois recortes a 300 dpi que decidiram os dois achados numéricos —
e um deles **corrigiu o escopo** de um achado que eu havia anunciado largo
demais lendo a página em 140 dpi.

### 3º — Ler a página inteira

Só para conteúdo **sem estrutura**: texto normativo corrido, definições,
condições de aplicabilidade, listas de hipóteses. É onde o OCR erra de um jeito
que nenhum recálculo detecta.

### 4º — Delegar a um fork quando o volume é grande

Documento longo e todo denso? **O trabalho de um subagente não entra na sua
janela** — só o resultado volta. Um fork lendo as páginas e devolvendo a
transcrição mantém dezenas de imagens fora daqui.

⚠️ **Fork, não modelo local.** Conferir dígito de tabela normativa é exatamente
onde um modelo mais fraco erra em silêncio, e o valor da conferência é pegar
erro sutil. Ver `delegacao-a-subagentes` para o que *pode* ir a modelo local —
dado confidencial, não julgamento numérico fino.

### O que não adianta

- **Mexer nas flags do docling.** `formula_enrichment` já vem ligado e faz o que
  pode; OCR de impresso escaneado erra `0`↔`O` e `/`↔`I` de qualquer forma.
- **Converter de novo com outras opções** esperando que o OCR melhore sozinho.
- **Ler tudo "por segurança".** Cobertura não conferida, declarada com honestidade
  no cabeçalho, é melhor que cobertura falsa comprada com a janela inteira.

## `format=zip` ou você perde as figuras

O endpoint `/convert` tem dois modos de resposta, e a escolha **não** é sobre
conveniência de download:

| | `format=json` (padrão da API) | `format=zip` |
|---|---|---|
| Markdown | sim | sim |
| Imagens extraídas | **descartadas** | **incluídas** |
| Campo `assets_dir` | nome de pasta **que já foi apagada** | — |

O serviço materializa as figuras num diretório temporário, referencia todas no
Markdown (`![Image](doc_assets/img_0000.png)`) e **apaga o diretório ao responder**.
Com `format=json` você recebe um Markdown com dezenas de links quebrados e um campo
`assets_dir` apontando para o nada. Não é que os assets "fiquem no servidor": eles
deixam de existir.

**Use sempre `format=zip`.** O script desta skill já faz isso, extrai o pacote e
reescreve os caminhos para a pasta local de assets.

## Flags que decidem custo e qualidade

Medido nesta base: artigo A4 de **71 páginas**, GPU RTX 3070, execuções aquecidas.

| Configuração | Tempo | Por página | Quando usar |
|---|---|---|---|
| base (layout + tabelas + OCR) | ~34 s | 0,48 s | localizar passagem, texto corrido |
| `formula_enrichment=true` | ~37 s | 0,52 s | **padrão para norma/artigo** — é o que dá LaTeX |
| `+ picture_description=true` | ~77 s | 1,08 s | quando as figuras precisam de descrição textual |

Duas leituras que importam:

- **Fórmulas custam pouco (~9%)** e são a razão de existir desta skill. Mantenha
  ligado. Vem ligado por padrão.
- **Descrever figuras mais que dobra o tempo.** Vem ligado por padrão. Se você só
  quer o texto e as equações, `picture_description=false` corta o tempo pela metade.
  A descrição serve para acessibilidade e indexação, não para conferir a figura —
  para conferir, extraia a página (ver `--paginas`).

### Qual modelo descreve as figuras

Quem descreve importa tanto quanto se descreve. Medido no mesmo fluxograma:

| `picture_description_model` | VRAM | O que produz |
|---|---|---|
| `smolvlm` *(padrão)* | 0,47 GiB | *"a diagram with some text and a few lines"* |
| `smolvlm-500m` | 0,95 GiB | *"a flowchart… connected with the labels 'Entrada' and 'Valido?'"* |
| `granite-api` | ~3 GB | *"a flowchart illustrating a decision-making process"* |
| `granite` | 5,54 GiB | não cabe em GPU de 8 GB — ver armadilhas |

O padrão descreve genericamente; **`smolvlm-500m` já lê rótulos** e custa pouco mais.
O `granite-api` serve o mesmo granite quantizado por um servidor local (Ollama) e dá a
melhor leitura, ao custo de exigir esse servidor no ar com o modelo puxado.

Nenhum deles substitui olhar a figura: descrição de VLM é indexável, **não é fonte para
citar valor**.

## Enhancement por LLM: não use em documento que será citado

O serviço oferece `enhance=true`, que passa o Markdown por um LLM para corrigir
artefatos de layout. Medido no golden set do serviço, com Ollama local: **o overall não
muda** — conserta um caption mesclado e, no mesmo passe, **corrompe conteúdo factual**.

No teste, "Mercúrio" virou **"Mercuryo"** — palavra que não existe em idioma nenhum. Os
números da tabela sobreviveram; o nome próprio, não.

Esse é o pior modo de falha possível para esta skill: **alteração silenciosa e
plausível**. Ninguém desconfia de "Mercuryo" no meio de vinte mil palavras, e o texto
segue para o relatório com aparência de correto. Mantenha `enhance=false` (é o padrão).
Se precisar da limpeza de layout, trate a saída como rascunho a conferir palavra por
palavra — o que anula a economia que motivaria usá-la.

## Fluxo

### 0. O serviço está no ar?

```bash
curl -s http://localhost:8010/health     # {"status":"ok","service":"docling-service"}
```

Sem isso, pare e avise — não caia silenciosamente para `pdftotext`, porque a
diferença de qualidade é justamente o motivo da skill.

### 1. Converter

```bash
uv run --with pikepdf --with requests python3 skills/dominio/docling-local/scripts/pdf2md.py \
    ~/refs/NORMA.pdf \
    --out base/refs/NORMA.md \
    --paginas 12,31,32,57 \
    --strip-regex "Customer: .*"
```

O script faz a triagem, decifra se preciso, converte em `zip`, grava o Markdown
**com as figuras ao lado**, limpa o ruído indicado, extrai as páginas pedidas como
PNG e escreve o cabeçalho de procedência — incluindo as flags usadas, para que a
extração diga em que condições foi feita.

Dois ajustes que valem conhecer:

- `--sem-figuras` corta o tempo pela metade em documento sem figuras relevantes.
- `--modelo-figuras` escolhe o VLM (default `smolvlm-500m`, que lê rótulos; use
  `granite-api` se o servidor local estiver no ar, para a melhor leitura).

O script **nunca** liga o `enhance` — ver a seção sobre enhancement acima.

### 2. Escrever a transcrição conferida

Aplique aqui a ordem de **Conferir barato**: recalcule primeiro, recorte depois,
página inteira só para texto sem estrutura.

Ao lado de `NORMA.md`, um `NORMA-<assunto>.md` com **o que você leu e conferiu**:
as equações que serão citadas, com tabela de símbolos; os valores lidos das
figuras; as passagens que sustentam o argumento, entre aspas. Marque
explicitamente o que **não** foi transcrito — é o que impede que o próximo leitor
suponha cobertura que não existe.

### 3. Registrar no índice

Acrescente a linha em `base/refs/README.md` (ou equivalente do projeto) apontando
os dois arquivos e o diretório de páginas.

## Armadilhas, todas custaram tempo

| Sintoma | Causa | Saída |
|---|---|---|
| `HTTP 500` + `{"error":"Nenhum arquivo .md gerado"}` | Mensagem genérica que **mascara a causa real**: PDF cifrado, OOM de VRAM ou falha do pipeline | Serviço atualizado devolve `detail`, `type` e `hint` no corpo — leia-os primeiro. Em serviço antigo, só resta `docker compose logs docling` |
| Markdown cheio de `![Image](..._assets/img_0000.png)` que não abrem | `format=json` **apagou** os assets | `format=zip`. O script já usa |
| `remove_headers_footers=true` não removeu nada | **Exige `enhance=true` e um `vision_provider`** — sozinho é inócuo. Serviço atualizado avisa em `warnings`; versões antigas ainda trazem default `true`, que sugere o contrário | Para rodapé repetido sem LLM, use `remove_blocks=true` ou `--strip-regex` |
| Conversão parece travada | É lenta mesmo: 0,5–1,1 s/página conforme as flags | Rodar em segundo plano, timeout largo (padrão 3600 s) |
| `picture_description_model=granite` → `CUDA out of memory` | Os pesos ocupam 5,54 GiB em bf16 e exigem **> 6,63 GiB livres** — inviável em GPU de 8 GB que também serve o desktop. Desligar o ambiente gráfico **não** resolve: libera ~1 GiB e ainda faltaria ~1 GiB | Use `smolvlm-500m`, ou `granite-api` para o mesmo modelo quantizado. Não adianta `expandable_segments` nem reduzir `batch_size`: o custo está nos pesos |
| `granite-api` falha dizendo que o endpoint está inacessível | O servidor de inferência local não está no ar, ou o modelo não foi puxado | `ollama pull granite3.2-vision:2b`. A falha é proposital: o serviço valida o endpoint **antes** de converter, para não devolver 90 figuras sem descrição em silêncio |
| Texto duplicado ao longo do arquivo | Documento *redline* (RLV): traz a edição anterior riscada e a nova | Normal. Registrar no cabeçalho e conferir qual versão você cita |
| Frases sem sentido, tabelas embaralhadas | PDF **digitalizado**: houve OCR | O script avisa quando não há camada de texto. Conferir contra a imagem |
| Rodapé repetido em todas as páginas | Carimbo de licença nominal | `remove_blocks=true` (regex por contagem, sem LLM) ou `--strip-regex` cirúrgico. **Mantenha a procedência no cabeçalho** |
| Janela de contexto some rápido convertendo documento longo | **Imagem lida fica no contexto** e é reenviada a cada requisição. 60 páginas lidas custam muito mais que 60 leituras | Ver **Conferir barato**: recalcular → recortar → página inteira → delegar a fork |
| Achado de "defeito na norma" que depois encolhe | Página lida a 140 dpi, ou escopo verificado menor que o escopo anunciado | Recorte a 300 dpi antes de afirmar; declare as linhas exatas conferidas |
| Tabelas complexas saem tortas no Markdown | Markdown não tem células mescladas | `--html` usa `export_to_html`, que gera `<table>` reais |

## Quando *não* usar esta skill

- **PDF de uma página, texto simples** — `pdftotext -layout` resolve em 200 ms.
- **Só localizar uma passagem** — `pdftotext | grep` é mais rápido e não gera
  arquivo que alguém terá de manter.
- **Documento sob NDA de terceiro** — o serviço é local, mas o `.md` resultante
  passa a viver no repositório e a entrar no contexto do agente. Ver
  [`secrets-guard`](../../secrets-guard/SKILL.md) e
  [`delegacao-a-subagentes`](../../delegacao-a-subagentes/SKILL.md).
- **Lote de documentos** — existe `/convert/batch`, que aceita múltiplos arquivos
  numa requisição e devolve um zip único. O script desta skill é de um arquivo por
  vez, porque a procedência é declarada por documento.

## Convenção de arquivos

```
base/refs/
├── NORMA.md              # extração integral, com cabeçalho de procedência
├── NORMA_assets/         # figuras extraídas pelo docling (vêm no zip)
│   └── img_0000.png
├── NORMA-<assunto>.md    # transcrição conferida: equações, tabelas, citações
└── NORMA_paginas/        # pag-012.png, pag-031.png — páginas inteiras p/ conferência
    └── pag-031.png
```

`_assets/` e `_paginas/` **não são redundantes**: o primeiro traz as figuras
recortadas pelo docling, útil para reinserir num relatório; o segundo traz a página
inteira renderizada, que é o que permite conferir um número contra o original, com
eixos, legenda e contexto ao redor.

O nome do assunto vem do recorte, não do documento: `IEC-60826-vento.md`,
`IEEE-738-formulas.md`. Um mesmo PDF pode render várias transcrições conferidas
conforme o projeto for precisando.

## Checklist antes de dar a extração por pronta

- [ ] Cabeçalho declara origem, data, ferramenta, páginas e **flags usadas**.
- [ ] Perdas declaradas: figuras ausentes, OCR, erros de stream, redline.
- [ ] Licença/procedência registrada se o PDF tiver carimbo.
- [ ] Figuras em `_assets/` e páginas críticas em `_paginas/`.
- [ ] Existe transcrição conferida ao lado, com o que **não** foi transcrito marcado.
- [ ] Nenhum número citado em outro documento saiu da extração integral sem
      conferência contra a imagem da página.
- [ ] **Toda tabela ou fórmula com estrutura matemática foi conferida por
      recálculo**, não só por leitura — é mais barato e é evidência mais forte.
- [ ] Dígito duvidoso foi relido em **recorte a 300 dpi** antes de virar achado.
      Anunciar defeito de norma com base em página a 140 dpi já deu errado.
- [ ] Achado de defeito na norma declara **o escopo exato** onde foi verificado.
      "Verifiquei nas linhas 15 a 50" não autoriza dizer "a tabela está errada":
      as linhas 7 a 14 podiam estar certas — e estavam.
