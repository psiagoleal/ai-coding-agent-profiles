---
name: apresentacao-html
description: >-
  Cria apresentações em HTML autocontido (um arquivo, abre sem rede) com
  narrativa de título-afirmação, temas trocáveis ou derivados de uma identidade
  visual, e visuais técnicos gerados por ferramenta: Mermaid, LaTeX, diagrama
  unifilar e circuito (schemdraw, CircuiTikZ), gráficos matplotlib, capturas e
  gravações de tela com Playwright, GIF e vídeo. Exporta PDF e PNG por slide.
  Aciona quando o usuário pedir apresentação, deck, slides, "apresentação HTML",
  material para reunião ou para projetar, ou quiser transformar uma análise em
  slides. Não aciona para documento corrido (spec, ADR, ATA) nem para deck
  publicado como Artifact quando houver dado de cliente.
metadata:
  origem:
    fonte: experiência profissional do mantenedor
    importada_em: 2026-11-17
    modificada: sim
---

# Apresentação HTML autocontida

Um deck é um argumento: a ideia central vem primeiro, cada slide prova uma
afirmação e o fim pede uma decisão. O template cuida da forma (canvas 16:9,
temas, navegação, impressão); esta skill cuida da ordem certa de trabalho e das
ferramentas para os visuais técnicos.

`<skill>` = `skills/dominio/apresentacao-html`. Comandos rodam a partir dele.

## Confidencialidade

- Projeto com dado de cliente: o deck fica **na máquina**. Não publicar como
  Artifact nem enviar a serviço externo. Se o material for do cliente (planilha,
  ATA, captura de tela com dado real), perguntar antes onde o deck será salvo.
- Exemplos e dados de demonstração são fictícios (IPs de documentação, valores
  inventados, marcados como fictícios no rodapé).
- Captura de app real: ambiente com dado fictício ou `--ocultar` nos campos sensíveis.

## Configuração (uma vez por máquina)

```bash
source <skill>/scripts/ambiente.sh      # caches e configuração dentro da skill
cd <skill> && npm install               # Mermaid, MathJax, Playwright, fontes
node node_modules/playwright-core/cli.js install ffmpeg   # só para gravar vídeo
node scripts/autoteste.mjs tudo          # cada etapa termina em "AUTOTESTE <etapa> OK"
```

Requisitos: Node 20+, Python 3, `uv`, Google Chrome (ou `CHROME_PATH`). LaTeX
só para CircuiTikZ. Caches e configuração ficam em `<skill>/.cache/`, nunca no
diretório do usuário (ADR 0011).

## Fluxo

### 1. Roteiro antes do design

Perguntar o que faltar (em bloco, uma vez): público, decisão ou entendimento
esperado, tempo disponível, projeção ou leitura, identidade visual exigida.
Depois escrever:

- a **ideia central** em uma frase;
- o **storyboard**: lista de títulos-afirmação, um por slide, que lida em
  sequência conta a história (situação → complicação → resposta → evidência →
  decisão pedida).

Para deck com mais de 5 slides, mostrar o storyboard e esperar aprovação antes
de construir. Detalhe e fontes em `references/boas-praticas.md`.

### 2. Tema

`python3 -I scripts/tema.py listar`. Padrão `tecnico`; `institucional` para
diretoria; `auditorio` para sala escura; `impressao` para PDF. Identidade
visual: `tema.py derivar --primaria "#hex" --verificar --gravar`. Ver
`references/temas.md`.

### 3. Slides

Copiar `templates/deck.html` para a pasta de trabalho (fora da skill, ex.:
`apresentacoes/<slug>/fonte.html`) e escrever os `<section class="slide">`.
Referência viva: `exemplos/deck-exemplo.html` (10 slides com todos os recursos).

| Layout (classe do `section`) | Uso |
|---|---|
| `capa` | título = ideia central; meta com autor, área, data |
| `numero` | um número grande + frase (`.valor`, `.unidade`) |
| `secao` | separador de bloco (`.num` + `h2`) |
| padrão | `header.cabecalho` (etiqueta + `h2` afirmação) + `.corpo` + `footer.rodape` |
| `figura` | figura ocupando o corpo |
| `citacao` | frase de decisão ou citação + `.callout` |

Corpo: `.duas-colunas`, `.texto-figura`, `.tres-colunas`, `.centro`.
Componentes: `.cartao`, `.callout`, `.chip.ok|alerta|erro|primaria`, `.destaque`,
`table` com `td.num` e `tr.destaque`, `pre.codigo`, `.equacao` + `dl.simbolos`,
`figure`/`figcaption`, `.passo` (revela no próximo clique), `aside.notas`
(notas do apresentador), `.fonte` no rodapé, `.num-slide` (numeração automática).

Regras de escrita:
- `h2` é frase completa com a conclusão, até 2 linhas.
- Corpo com no máximo ~3 itens curtos ou um visual; o resto vai em `.notas`.
- Toda figura com `alt` descrevendo o que mostra; todo número com unidade e fonte.

### 4. Visuais

Escolha pela necessidade; comandos, opções e alternativas em
`references/ferramentas.md`.

| Necessidade | Ferramenta |
|---|---|
| fluxo, sequência, estados | `<pre class="mermaid">` direto no fonte |
| equação | `<span class="tex">` / `<div class="tex-bloco">` (LaTeX) |
| unifilar, circuito simples | schemdraw (`exemplos/figuras.py`) |
| circuito de publicação | CircuiTikZ + `dvisvgm` (`exemplos/circuito.tex`) |
| gráfico, fasorial | matplotlib + `scripts/estilo_mpl.py` |
| tela de sistema web | `scripts/captura.mjs pagina … --seletor` |
| fluxo de tela em movimento | `captura.mjs video --roteiro` → `scripts/gif.py` |

Figuras SVG geradas no mesmo tema inicial do deck e incluídas com
`<img src="x.svg" data-inline alt="…">` acompanham a troca de tema. Arte em
preto: `data-inline="monocromatico"`.

### 5. Construir, exportar, revisar

```bash
python3 -I scripts/tema.py verificar                               # contraste AA
node scripts/construir.mjs fonte.html <slug>.html --estrito        # arquivo único
node scripts/captura.mjs deck <slug>.html revisao/ --pdf <slug>.pdf
node scripts/captura.mjs deck <slug>.html revisao-escuro/ --tema auditorio
```

Revisar os PNG de `revisao/` contra o checklist de `references/boas-praticas.md`
(seção 6). Imagens são lidas por subagente, não no contexto principal: cada
PNG custa caro em contexto e a sessão principal só precisa do veredito. Pedir ao subagente só problemas concretos: texto
cortado, sobreposição, contraste, espaço vazio, render quebrado. Corrigir e
exportar de novo uma vez.

### 6. Entregar

Entregar `<slug>.html` (abre sem rede) e `<slug>.pdf`, com o caminho completo.
Dizer em uma linha o tema, o número de slides e o que ficou pendente.

## Na apresentação

`→`/espaço avança (revela passos antes de trocar de slide), `←` volta,
`Home`/`End`, `T` troca tema, `N` notas com cronômetro, `L` modo leitura
(todos os slides com notas), `F` tela cheia, `#5` na URL abre no slide 5,
`?tema=auditorio` e `?modo=leitura` na URL. Toque: deslizar.

## Manutenção

- `temas.json` é a fonte dos temas; `tema.py aplicar` regrava o bloco
  `/* TEMAS:inicio */ … /* TEMAS:fim */` de um HTML.
- Mudou CSS ou script do template: copiar o mesmo bloco para
  `exemplos/deck-exemplo.html` (o autoteste `estrutura` acusa divergência).
- `node scripts/autoteste.mjs tudo` depois de qualquer mudança.
