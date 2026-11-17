# Temas e identidade visual

`temas.json` é a fonte única. Dele saem: o CSS do deck (`tema.py css|aplicar`),
as cores do Mermaid e dos SVG embutidos (`construir.mjs`), o estilo dos gráficos
(`estilo_mpl.py`) e as fontes embutidas (`@fontsource` em `node_modules`).

## Tokens

| Token | Papel |
|---|---|
| `fundo`, `superficie` | fundo do slide; cartões, células, callout |
| `texto`, `suave` | texto principal; texto secundário, eixos, rodapé |
| `linha` | fios de tabela e bordas |
| `primaria`, `primaria-suave`, `sobre-primaria` | cor da marca; fundo leve dela; texto sobre a primária (capa) |
| `enfase` | a mensagem do slide: barra destacada, `.destaque`, callout |
| `cinza` | séries de contexto em gráfico |
| `ok`, `alerta`, `erro` | estado (chips); não substituem a ênfase |
| `codigo` | fundo de bloco de código |
| fontes `titulo`, `texto`, `mono` | famílias; precisam existir em `@fontsource` para serem embutidas |

## Temas prontos

| Tema | Quando usar |
|---|---|
| `tecnico` | padrão: reunião de engenharia, sala iluminada |
| `institucional` | gestão e diretoria; títulos serifados, tom sóbrio |
| `auditorio` | projeção em sala escura (fundo escuro) |
| `impressao` | PDF para distribuir e leitura; legível em preto e branco |

O deck carrega todos os temas listados em `data-temas`; `T` alterna na hora,
`?tema=nome` abre num tema. Para reduzir tamanho e fontes, construir com
`--temas tecnico,auditorio`.

## Tema a partir de uma identidade visual

1. Pegar a cor primária oficial da marca (e a secundária, se houver).
2. Derivar e verificar:

```bash
python3 -I scripts/tema.py derivar --nome marca --primaria "#c8102e" \
  [--enfase "#hex"] [--modo claro|escuro] \
  [--fonte-titulo "Inter"] [--fonte-texto "IBM Plex Sans"] --verificar --gravar
```

   - neutros com leve viés da matiz da marca;
   - primária e ênfase escurecidas (ou clareadas no escuro) só o necessário para
     4,5:1, preservando matiz e saturação;
   - sem `--enfase`, usa a matiz complementar.
3. Conferir à mão em `temas.json` e ajustar o que a marca exige (ex.: cor exata
   na capa). Rodar `tema.py verificar` de novo.
4. `tema.py aplicar fonte.html` e reconstruir.

**Fonte da marca fora do `@fontsource`:** declarar `@font-face` no `<style>` do
deck apontando para o `.woff2` local (`url(fontes/Marca-Regular.woff2)`);
`construir.mjs` embute o arquivo. Confirmar a licença da fonte para embutir.

**Logotipo:** `<img class="logo" src="marca.svg" alt="…">` na capa; SVG de
preferência. Logotipo é isento da regra de contraste (WCAG), mas precisa de
área livre em volta.

## Cores em figuras

- Gerar figura no **mesmo tema inicial** do deck (`--tema`). Com
  `<img … data-inline>`, `construir.mjs` troca as cores do tema por `var(--token)`
  e a figura acompanha o `T`.
- Arte em preto (TikZ, Graphviz, PlantUML): `data-inline="monocromatico"` troca
  preto por `currentColor` com a cor de texto do tema.
- PNG/JPG (capturas de tela) não mudam de tema: escolha um fundo neutro ou use
  moldura (`.cartao`).

## Escuro × claro

Escuro (`auditorio`) em sala escura reduz ofuscamento; claro em sala iluminada
lê melhor. Para PDF e impressão, sempre claro (`impressao`). Na dúvida, levar os
dois: o deck troca com `T`.
