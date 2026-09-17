---
name: mockup-lab
description: >-
  Prototipagem rápida de telas/componentes de UI em HTML/CSS, com renderização
  de variantes via browser headless para comparação visual, e exportação da
  variante aprovada como SVG importável em um Penpot self-hosted. Aciona
  quando o usuário pedir para prototipar, mockar, comparar variantes de
  layout, ou levar um design aprovado para o Penpot.
---

# mockup-lab — Prototipagem de UI com Penpot como registro

Duas fases implementadas (Fase 1 e Fase 2). Uma terceira fase (manipulação
direta do canvas do Penpot via Plugin API) está documentada ao final como
referência técnica, mas **não implementada** — exige infraestrutura adicional
(servidor MCP + plugin conectado a uma sessão de navegador ativa) e deve ser
tratada como evolução futura, não como ponto de partida.

## Por que HTML/CSS antes de Penpot

Gerar variações direto em código é o loop de menor atrito para decisão de
interface: o agente escreve, renderiza, e você compara screenshots — sem
precisar abrir o Penpot a cada iteração. O Penpot entra depois, como o
registro "oficial" do layout já aprovado.

## Setup (uma vez por máquina)

```bash
cd skills/dominio/mockup-lab
npm install
npx playwright install chromium
```

## Fase 1 — gerar e comparar variantes

1. Crie um diretório de trabalho fora da skill, no projeto onde o mockup faz
   sentido: `mockups/<slug-da-tela>/variants/`.
2. Para cada variante, copie `templates/variant-base.html` e edite livremente
   (HTML/CSS puro por padrão; Tailwind via CDN é aceitável se acelerar a
   iteração — adicione o `<script src="https://cdn.tailwindcss.com">` você
   mesmo, não está no template para manter a base sem dependências de rede).
   Nomeie os arquivos de forma descritiva: `variant-a-sidebar.html`,
   `variant-b-topnav.html`, etc.
3. Renderize todas as variantes:
   ```bash
   node skills/dominio/mockup-lab/scripts/render-variants.mjs \
     --input mockups/<slug>/variants \
     --output mockups/<slug>/renders \
     --viewports 1440x900,390x844
   ```
   Gera um PNG por variante × viewport em `mockups/<slug>/renders/`.
4. Leia os PNGs gerados (ferramenta `Read` funciona com imagens) e apresente-os
   ao usuário para comparação. Itere: edite as variantes, rode de novo.
5. Não avance para a Fase 2 até o usuário confirmar explicitamente qual
   variante (e em qual viewport) foi aprovada.

## Fase 2 — exportar a variante aprovada para o Penpot

O Penpot importa SVG de forma fiel (formato aberto nativo). A conversão usa a
biblioteca [`dom-to-svg`](https://github.com/felixfbecker/dom-to-svg), que
serializa o DOM renderizado (posições, cores, texto, imagens inline) em SVG —
rodando dentro do próprio contexto do browser via Playwright, carregada de
`esm.sh` em tempo de execução (requer acesso à internet no momento do
export; não precisa estar instalada localmente).

```bash
node skills/dominio/mockup-lab/scripts/export-svg-for-penpot.mjs \
  --input mockups/<slug>/variants/variant-a-sidebar.html \
  --viewport 1440x900 \
  --output mockups/<slug>/export/variant-a-sidebar.svg
```

Depois, leve o SVG para dentro de um arquivo do Penpot. Duas formas:

### 2a. Manual
Abra o projeto de destino no Penpot e cole o conteúdo do `.svg` dentro do
canvas de um arquivo (copiar o texto do SVG e `Ctrl+V` no workspace — **não**
é o "Import files" do menu de projetos, que só aceita `.penpot`/`.zip`).

### 2b. Automatizado (recomendado quando já configurado)
Requer login uma única vez por máquina, já que o Penpot desta instância só
responde por hostname (`penpot.lan`), não pelo IP puro — os scripts cuidam
disso via `--host-resolver-rules` do Chromium, sem tocar em `/etc/hosts`.

```bash
# uma vez: abre um Chromium visível para você logar manualmente; salva a
# sessão num perfil persistente em ~/.config/mockup-lab/penpot-profile
node skills/dominio/mockup-lab/scripts/penpot-login.mjs
# (janela fica aberta até você criar o arquivo de sinal indicado no log,
# ou até 30 min — avise quando tiver logado para o sinal ser criado)

# a cada export aprovado:
node skills/dominio/mockup-lab/scripts/import-svg-to-penpot.mjs \
  --svg mockups/<slug>/export/variant-a-sidebar.svg \
  --file-name "<slug> - variant-a-sidebar" \
  --project Drafts
```

O script cria um arquivo novo no projeto indicado (padrão `Drafts`), renomeia
e "cola" o SVG via um evento `paste` sintético — o mesmo mecanismo que o
Penpot usa quando você copia/cola SVG manualmente no canvas — o que resulta
em camadas nativas editáveis, não uma imagem embutida.

**Cuidados específicos deste fluxo:**
- `~/.config/mockup-lab/penpot-profile` contém a sessão (cookies) — trate
  como uma credencial: não versionar, não compartilhar, permissões 700.
  **Este caminho fora do repositório é exceção deliberada** à regra repo-local
  (ADR 0011): sessão é segredo, e segredo guardado dentro do repositório acaba
  commitado. A regra vale para estado, cache e aprovação — não para credencial.
  Recriar com `penpot-login.mjs` sempre que a sessão expirar (o script de
  import avisa se cair na tela de login).
- O Penpot sincroniza a mudança para o backend via websocket de forma
  assíncrona/debounced. O script espera alguns segundos após a colagem antes
  de fechar o browser — fechar cedo demais **perde o import silenciosamente**
  (o script reporta sucesso, mas o arquivo fica vazio). Se notar isso
  acontecendo de novo, aumente a espera em `import-svg-to-penpot.mjs` antes de
  `context.close()`.
- Ajuste as constantes `PENPOT_HOST`/`PENPOT_IP` no topo dos dois scripts se
  o endereço da instância mudar.

**Limitações conhecidas (ambos os caminhos), verifique visualmente após cada export:**
- `dom-to-svg` não é mantido ativamente (~5 anos sem release); fidelidade de
  CSS Grid/Flexbox complexo pode ser imperfeita — compare o SVG importado
  com o screenshot da Fase 1 antes de considerar o export "pronto".
- É uma captura estática de UM viewport — não reproduz responsividade nem
  estados de interação (hover, foco). Se precisar de múltiplos breakpoints no
  Penpot, exporte um SVG por viewport.
- Fontes/imagens externas são inlined como data URIs pelo `inlineResources`;
  arquivos SVG resultantes podem ficar grandes.

## Definição de pronto da skill

- [ ] Variantes da Fase 1 renderizadas e comparadas antes de qualquer decisão.
- [ ] Usuário confirmou explicitamente a variante aprovada antes do export.
- [ ] SVG exportado foi conferido visualmente contra o screenshot original.
- [ ] Import no Penpot confirmado visualmente (manual ou via
      `import-svg-to-penpot.mjs`) — nos dois casos, abrir o arquivo resultante
      e comparar com o screenshot da Fase 1 antes de considerar pronto.

---

## Fase 3 (referência técnica, não implementada) — Plugin API do Penpot

Notas de uma investigação já feita, para não repetir a pesquisa numa sessão
futura caso decidam avançar para manipulação direta do canvas:

- **Modelo de execução**: plugins rodam dentro de um iframe isolado, como
  parte da própria sessão web do Penpot — não é headless nem invocável
  diretamente por CLI. Comunicação Penpot ↔ plugin via `postMessage`.
  O objeto global `penpot` só existe no arquivo `plugin.ts`/`plugin.js`
  (compilado); a UI do plugin é um iframe HTML separado que troca mensagens
  com ele via `penpot.ui.onMessage` / `postMessage`.
- **Hospedagem**: cada plugin é hospedado fora do Penpot (URL de manifest
  própria); instala-se via Ctrl+Alt+P (ou ⌘+Alt+P) apontando para o
  `manifest.json`.
- **`manifest.json`** (v2, permite paths relativos):
  ```json
  {
    "name": "…", "description": "…", "version": 2, "code": "plugin.js",
    "icon": "…",
    "permissions": [
      "content:read", "content:write", "library:read", "library:write",
      "user:read", "comment:read", "comment:write",
      "allow:downloads", "allow:localstorage"
    ]
  }
  ```
  (permissão de escrita já inclui a de leitura correspondente)
- **API de shapes** (confirmada em
  [`penpot-plugins-samples/create-shape`](https://github.com/penpot/penpot-plugins-samples/tree/main/create-shape)):
  `penpot.createRectangle()`, `createEllipse()`, `createPath()`,
  `createBoard()`; shape resultante tem `.resize(w, h)`, `.x`/`.y`, `.name`,
  `.fills = [{ fillColor }]`, `.strokes = [...]`, `.borderRadius`.
  `penpot.viewport.center` dá o centro da viewport atual para posicionar.
- **Chamadas de rede saindo do plugin funcionam**: o exemplo
  [`third-party-api`](https://github.com/penpot/penpot-plugins-samples/tree/main/third-party-api)
  faz `fetch()` para uma API externa e usa `penpot.uploadMediaUrl(name, url)`
  para trazer imagens como fill — prova de que o padrão "ponte MCP → plugin"
  (um servidor MCP local que o plugin consulta via chamada de saída) é
  arquiteturalmente viável, ainda que a implementação de terceiros específica
  vista numa pesquisa (`penpot-mcp`) não tenha sido verificada em detalhe.
- **Outros exemplos relevantes no samples repo**: `create-flexlayout`,
  `create-gridlayout`, `components-library`, `colors-library` (tokens),
  `create-interactive-prototype`. Templates iniciais:
  [`penpot-plugin-starter-template`](https://github.com/penpot/penpot-plugin-starter-template)
  (TS vanilla) e [`plugin-examples`](https://github.com/penpot/plugin-examples)
  (Angular/Vue/React).
- **Automação complementar (sem plugin)**: `penpot-export` (CLI oficial) já
  exporta tokens de design (cor, tipografia, espaçamento) de um arquivo Penpot
  para CSS/SCSS/JSON — útil para manter a Fase 1 visualmente alinhada ao
  design system do Penpot, sem precisar da Plugin API.

Se decidirem avançar para a Fase 3: o ponto de partida é o
`penpot-plugin-starter-template`, não a ponte MCP de terceiros — construir a
ponte própria dá controle sobre o protocolo e evita depender de um projeto
comunitário não auditado.
