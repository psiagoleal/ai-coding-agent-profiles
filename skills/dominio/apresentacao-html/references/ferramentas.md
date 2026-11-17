# Ferramentas por necessidade

**Verificado** = exercitado pelo `autoteste.mjs` nesta máquina (Linux, GNOME
Wayland, Chrome, Node 24, TeX Live). **Alternativa** = opção conhecida, não
instalada nem testada aqui; confirmar versão e licença antes de adotar.

Toda saída vira SVG (vetorial, nítido no projetor, tema via `data-inline`) ou,
para captura de tela, PNG. Dentro do deck tudo é embutido por `construir.mjs`.

## Mapa rápido

| Preciso de | Use | Estado | Entra no deck como |
|---|---|---|---|
| Fluxograma, sequência, estados, Gantt, ER | Mermaid 11 | Verificado | `<pre class="mermaid">` no fonte |
| Equação | LaTeX via MathJax 3 (SVG) | Verificado | `<span class="tex">` ou `<div class="tex-bloco">` |
| Diagrama unifilar, circuito simples, lógica | schemdraw 0.19 (Python) | Verificado | `<img src="x.svg" data-inline>` |
| Circuito com qualidade de publicação | CircuiTikZ (LaTeX) + dvisvgm | Verificado | `<img src="x.svg" data-inline="monocromatico">` |
| Gráfico estático | matplotlib 3.9 + `estilo_mpl.py` | Verificado | `<img src="x.svg" data-inline>` |
| Diagrama fasorial | matplotlib (`annotate` com setas) | Verificado | `<img src="x.svg" data-inline>` |
| Captura de app web | Playwright (`captura.mjs pagina`) | Verificado | `<img src="x.png">` |
| Gravação de app web | Playwright (`captura.mjs video` + roteiro) | Verificado | `.mp4` ou `.gif` via `gif.py` |
| GIF / vídeo leve | ffmpeg do imageio-ffmpeg (`gif.py`) | Verificado | `<img>` (gif) ou `<video autoplay loop muted playsinline>` |
| PDF e PNG por slide | `captura.mjs deck --pdf` | Verificado | entrega |
| Grafo e árvore com layout automático | Graphviz (`dot -Tsvg`), D2 | Alternativa | `data-inline="monocromatico"` |
| Arquitetura e UML | PlantUML, Mermaid C4 | Alternativa | SVG |
| Esboço à mão livre | Excalidraw (exportar SVG) | Alternativa | SVG |
| Rede elétrica a partir de dados | pandapower (`simple_plot`), PyPSA (`plot`) | Alternativa | SVG via matplotlib |
| Circuito a partir de netlist, com análise | lcapy (gera CircuiTikZ) | Alternativa | SVG via CircuiTikZ |
| Gráfico interativo | ECharts, Chart.js, Vega-Lite, Plotly | Alternativa | bundle JS local; ver "Interativo" |

## Configuração (uma vez)

```bash
cd skills/dominio/apresentacao-html
source scripts/ambiente.sh                 # caches dentro da skill
npm install                                # Mermaid, MathJax, Playwright, fontes
node node_modules/playwright-core/cli.js install ffmpeg   # só para gravar vídeo
node scripts/autoteste.mjs tudo            # confere tudo
```

Python roda isolado pela função `py` (uv, Python 3.12, matplotlib, schemdraw,
imageio-ffmpeg) sem instalar nada no sistema. O navegador é o Chrome instalado
(`CHROME_PATH` aponta outro Chromium).

## Diagramas

**Mermaid**: escrever direto no fonte. `construir.mjs` renderiza com o tema e
troca as cores por variáveis.

```html
<pre class="mermaid" data-titulo="Fluxo de aprovação">
flowchart LR
  A[BOQ] --> B[RFP] --> C{Aprovação técnica}
  C -->|sim| D[Equalização]
</pre>
```

Use `&lt;`/`&gt;` dentro do bloco se o HTML exigir; o script desescapa. Para
diagrama grande, dividir em dois slides em vez de diminuir a fonte.

**Graphviz / PlantUML (alternativa)**: gerar SVG fora (`dot -Tsvg in.dot -o x.svg`)
e incluir com `data-inline="monocromatico"`.

## Equações

```html
<div class="tex-bloco">\bar S = \dot V\,\dot I^{*} = P + jQ</div>   <!-- destacada -->
texto com <span class="tex">X_{L} = \omega L</span> no meio              <!-- na linha -->
```

MathJax gera SVG sem fonte externa (`fontCache: none`) e herda a cor do texto.
Erro de LaTeX interrompe a construção com a mensagem do MathJax. Pacotes
disponíveis: os do `tex-svg-full` (AMS, physics, mhchem, entre outros).

## Sistemas elétricos

**schemdraw** (Python, verificado): elementos prontos (`Resistor`, `Inductor`,
`Capacitor`, `Transformer`, `Switch`, `Breaker`, `SourceSin`, `Ground`, `Dot`,
`Arrow`) e elementos próprios. `exemplos/figuras.py` mostra um unifilar com
disjuntor (quadrado) e transformador (dois círculos) definidos como
`Element2Term`. Configurar com `estilo_mpl.schemdraw_config(tema)`.

**CircuiTikZ** (verificado): melhor tipografia e símbolos IEC/ANSI.

```bash
latex -interaction=nonstopmode -halt-on-error circuito.tex
dvisvgm --no-fonts --exact-bbox circuito.dvi -o circuito.svg   # glifos viram caminhos
```

`exemplos/circuito.tex` usa `standalone` + `circuitikz[european]`. A opção
`siunitx` exige o pacote `siunitx` (não instalado aqui). `\text{}` em rótulo
pede `amsmath`.

**Fasorial**: matplotlib com `annotate(arrowprops=…)`, eixo igual (`set_aspect('equal')`),
rótulos com `$\dot V$` (mathtext). Exemplo em `exemplos/figuras.py`.

**Redes (alternativa)**: pandapower `plotting.simple_plot(net)` e PyPSA
`network.plot()` desenham a topologia a partir do modelo; salvar em SVG com o
estilo do tema.

## Gráficos

`estilo_mpl.aplicar(tema)` configura matplotlib: fundo transparente, sem moldura
superior/direita, ciclo de cores (primária, cinza, ênfase, suave), texto como
texto no SVG (`svg.fonttype: none`, usa a fonte do deck). `estilo_mpl.salvar(fig, caminho)`.

Padrão de barra com mensagem: tudo em `cores["cinza"]`, a barra que importa em
`cores["enfase"]`, valor escrito na ponta, sem legenda. Ver `barras()` em
`exemplos/figuras.py`.

**Interativo (alternativa)**: só se a interação for a mensagem. Instalar o pacote
(`npm install chart.js@4.4.7`), referenciar o bundle UMD local
(`<script src="node_modules/chart.js/dist/chart.umd.js">`) e deixar o
`construir.mjs` embutir. Plotly em HTML autocontido custa ~3 MB.

## Captura de tela e gravação

### Web (Playwright, verificado)

```bash
# página inteira ou só um elemento, em 2x
node scripts/captura.mjs pagina http://localhost:5173/rfp saida/rfp.png --seletor "main table" --escala 2
# destacar e ocultar
node scripts/captura.mjs pagina URL saida.png --destacar ".botao-enviar" --ocultar ".email, .cnpj"
# gravar um fluxo
node scripts/captura.mjs video URL saida.webm --roteiro roteiro.json --largura 1280 --altura 720
```

Roteiro: lista de passos `ir`, `clicar`, `digitar`, `tecla`, `rolar`, `esperar`,
`esperarSeletor` (ver `exemplos/roteiro.json`). App com login: gerar um
`storageState` uma vez fora do repositório e passar `--estado arquivo.json`;
nunca senha em argumento ou roteiro. Para dado de cliente na tela, usar ambiente
com dados fictícios ou `--ocultar`.

### Desktop

| Ambiente | Captura | Gravação | Estado |
|---|---|---|---|
| GNOME Wayland (esta máquina) | `PrtSc` (ferramenta do GNOME); `gnome-screenshot` via portal | `Ctrl+Shift+Alt+R` (gravador do GNOME, gera .webm) | Alternativa; manual |
| wlroots (Sway, Hyprland) | `grim -g "$(slurp)" x.png` | `wf-recorder -g "$(slurp)" -f x.mp4` | grim e slurp instalados, mas não funcionam no GNOME |
| X11 | `scrot -s x.png`, `import x.png` (ImageMagick) | `ffmpeg -f x11grab -i :0.0 x.mp4`; `xdotool` automatiza cliques | Alternativa |
| Windows / WSL | `Win+Shift+S`; ShareX (captura e GIF) | ShareX, Xbox Game Bar (`Win+G`) | Alternativa |
| Terminal | — | `asciinema rec` + `agg` (GIF); VHS (`.tape` → GIF/MP4) | Alternativa |

Qualquer gravação (.webm, .mp4, .mkv) entra no deck por `gif.py`.

Numa sessão interativa com a extensão Claude in Chrome, a ferramenta
`gif_creator` grava uma sequência de ações no navegador real do usuário. Usar só
quando o Playwright headless não alcançar o app (ex.: login com SSO).

### GIF e vídeo

```bash
py scripts/gif.py gravacao.webm demo.gif --largura 960 --fps 12 --inicio 2 --duracao 8
py scripts/gif.py gravacao.webm demo.mp4            # H.264, menor e mais nítido que GIF
py scripts/gif.py --de-imagens "slides/slide-0*.png" resumo.gif --segundos 2
```

GIF usa paleta própria (palettegen/paletteuse). Acima de ~10 s ou 5 MB, prefira
`.mp4` com `<video src="demo.mp4" autoplay loop muted playsinline>`. gifski gera
GIF menor, mas a licença exige atenção em uso comercial fechado.

## Autocontido

`construir.mjs fonte.html saida.html --estrito`:

- aplica os temas de `temas.json`;
- renderiza Mermaid e LaTeX em SVG;
- embute `.woff2` (subconjunto latin) das fontes dos temas;
- embute CSS, JS, imagens, vídeos e `url()` locais como data URI;
- `data-inline` põe o SVG no HTML com ids prefixados e cores do tema;
- `--estrito` falha com qualquer recurso externo; limite padrão 15 MB (`--max-mb`).

Equivalente genérico para páginas prontas: `monolith` (Rust) empacota uma página
em um HTML só, mas não executa JS; aqui não é necessário.
