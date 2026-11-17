#!/usr/bin/env node
// Autoteste da skill. Cada etapa imprime "AUTOTESTE <etapa> OK" só se tudo passar.
// uso: node autoteste.mjs estrutura|graficos|construcao|exportacao|midia|home|tudo
import { execFileSync } from 'node:child_process';
import { existsSync, mkdirSync, readFileSync, readdirSync, rmSync, statSync } from 'node:fs';
import { join } from 'node:path';
import { RAIZ, CACHE } from './comum.mjs';

const SAIDA = join(CACHE, 'autoteste');
const EXEMPLO = join(RAIZ, 'exemplos', 'deck-exemplo.html');
const FIGURAS = join(RAIZ, 'exemplos', 'figuras');

function falha(msg) { console.error(`FALHA ${msg}`); process.exit(1); }
function afirmar(cond, msg) { if (!cond) falha(msg); }
function rodar(cmd, args, opcoes = {}) {
  try {
    return execFileSync(cmd, args, { cwd: RAIZ, encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], ...opcoes });
  } catch (e) {
    falha(`${cmd} ${args.join(' ').slice(0, 160)}\n${(e.stdout || '') + (e.stderr || '')}`.slice(0, 2000));
  }
}
const py = (...args) => rodar('bash', ['-c', `source scripts/ambiente.sh && py ${args.map((a) => `'${a}'`).join(' ')}`]);
const node = (...args) => rodar(process.execPath, args);
const tamanho = (f) => (existsSync(f) ? statSync(f).size : 0);
const blocos = (html, tag) => [...html.matchAll(new RegExp(`<${tag}>[\\s\\S]*?</${tag}>`, 'g'))].map((m) => m[0]);

function estrutura() {
  const exigidos = [
    'SKILL.md', 'temas.json', 'package.json', 'templates/deck.html',
    'references/boas-praticas.md', 'references/ferramentas.md', 'references/temas.md',
    'scripts/tema.py', 'scripts/construir.mjs', 'scripts/captura.mjs', 'scripts/gif.py',
    'scripts/estilo_mpl.py', 'scripts/ambiente.sh', 'scripts/comum.mjs', 'scripts/caminhos.mjs',
    'exemplos/deck-exemplo.html', 'exemplos/figuras.py',
  ];
  for (const f of exigidos) afirmar(tamanho(join(RAIZ, f)) > 200, `arquivo ausente ou vazio: ${f}`);
  const skill = readFileSync(join(RAIZ, 'SKILL.md'), 'utf8');
  afirmar(/^---\nname: apresentacao-html\ndescription: [\s\S]+?\n---\n/.test(skill), 'frontmatter do SKILL.md');
  afirmar(skill.split('\n').length <= 500, 'SKILL.md acima de 500 linhas');
  for (const ref of ['references/boas-praticas.md', 'references/ferramentas.md', 'references/temas.md']) {
    afirmar(skill.includes(ref), `SKILL.md não aponta para ${ref}`);
  }
  const tpl = readFileSync(join(RAIZ, 'templates', 'deck.html'), 'utf8').replace(/\/\* TEMAS:inicio \*\/[\s\S]*?\/\* TEMAS:fim \*\//, '');
  const ex = readFileSync(EXEMPLO, 'utf8').replace(/\/\* TEMAS:inicio \*\/[\s\S]*?\/\* TEMAS:fim \*\//, '');
  afirmar(blocos(tpl, 'style')[0] === blocos(ex, 'style')[0], 'CSS do exemplo divergiu do template');
  afirmar(blocos(tpl, 'script')[0] === blocos(ex, 'script')[0], 'script do exemplo divergiu do template');
  console.log(`${exigidos.length} arquivos; template e exemplo sincronizados`);
}

function graficos() {
  const out = py('exemplos/figuras.py', FIGURAS, '--tema', 'tecnico');
  afirmar(out.includes('FIGURAS OK'), 'figuras.py não terminou');
  // CircuiTikZ: latex + dvisvgm (glifos viram caminhos, SVG autocontido).
  const tmp = join(CACHE, 'tmp-tex');
  rmSync(tmp, { recursive: true, force: true });
  mkdirSync(tmp, { recursive: true });
  rodar('latex', ['-interaction=nonstopmode', '-halt-on-error', join(RAIZ, 'exemplos', 'circuito.tex')], { cwd: tmp });
  rodar('dvisvgm', ['--no-fonts', '--exact-bbox', join(tmp, 'circuito.dvi'), '-o', join(FIGURAS, 'circuito.svg')], { cwd: tmp });
  rmSync(tmp, { recursive: true, force: true });
  const primaria = JSON.parse(readFileSync(join(RAIZ, 'temas.json'), 'utf8')).temas.tecnico.cores.primaria;
  for (const f of ['unifilar.svg', 'barras.svg', 'fasorial.svg', 'circuito.svg']) {
    const svg = readFileSync(join(FIGURAS, f), 'utf8');
    afirmar(svg.includes('<svg') && svg.length > 1500, `${f} vazio`);
    afirmar(/viewBox=/.test(svg), `${f} sem viewBox (não escala no slide)`);
    if (f === 'unifilar.svg') afirmar(svg.toLowerCase().includes(primaria), `${f} sem a cor do tema`);
  }
  console.log('4 SVG gerados (schemdraw, matplotlib x2, CircuiTikZ)');
}

function construcao() {
  if (!existsSync(join(FIGURAS, 'unifilar.svg'))) graficos();
  mkdirSync(SAIDA, { recursive: true });
  const destino = join(SAIDA, 'deck.html');
  const out = node('scripts/construir.mjs', EXEMPLO, destino, '--estrito');
  afirmar(out.includes('CONSTRUCAO OK'), 'construir não confirmou');
  const html = readFileSync(destino, 'utf8');
  afirmar(!/<pre[^>]*class="mermaid"/.test(html), 'Mermaid ficou em texto');
  const fonteTex = readFileSync(EXEMPLO, 'utf8').match(/class="tex(-bloco)?[\s"]/g).length;
  const texSvg = (html.match(/class="tex(-bloco)?[^"]*"[^>]*><svg/g) || []).length;
  afirmar(texSvg === fonteTex, `LaTeX: ${texSvg} de ${fonteTex} renderizados`);
  afirmar((html.match(/class="diagrama"[^>]*><svg/g) || []).length === 1, 'diagrama Mermaid ausente');
  afirmar(!/data-inline/.test(html), 'imagem data-inline não foi embutida');
  afirmar(/fill="currentColor" style="color:var\(--texto\)"/.test(html), 'SVG monocromático sem cor do tema');
  afirmar((html.match(/@font-face/g) || []).length >= 8, 'fontes não embutidas');
  afirmar(!/(src|href)=["'](https?:)?\/\//i.test(html), 'há recurso externo');
  afirmar(/var\(--primaria/.test(html), 'SVG sem variáveis de tema');
  console.log(`latex ${texSvg}/${fonteTex}, mermaid 1, ${(html.length / 1024).toFixed(0)} KB`);
}

function exportacao() {
  const deck = join(SAIDA, 'deck.html');
  if (!existsSync(deck)) construcao();
  const pasta = join(SAIDA, 'slides');
  rmSync(pasta, { recursive: true, force: true });
  const pdf = join(SAIDA, 'deck.pdf');
  node('scripts/captura.mjs', 'deck', deck, pasta, '--pdf', pdf);
  const esperado = (readFileSync(EXEMPLO, 'utf8').match(/<section class="slide/g) || []).length;
  const pngs = readdirSync(pasta).filter((f) => f.endsWith('.png'));
  afirmar(pngs.length === esperado, `PNG: ${pngs.length} de ${esperado}`);
  const paginas = (readFileSync(pdf, 'latin1').match(/\/Type\s*\/Page[^s]/g) || []).length;
  afirmar(paginas === esperado, `PDF: ${paginas} páginas para ${esperado} slides`);
  console.log(`${esperado} slides -> ${pngs.length} PNG e ${paginas} páginas de PDF`);
}

function midia() {
  const deck = join(SAIDA, 'deck.html');
  if (!existsSync(deck)) construcao();
  const pasta = join(SAIDA, 'midia');
  rmSync(pasta, { recursive: true, force: true });
  mkdirSync(pasta, { recursive: true });
  const secoes = readFileSync(EXEMPLO, 'utf8').split(/<section class="slide/).slice(1);
  const nTabela = secoes.findIndex((s) => s.includes('<table')) + 1;
  afirmar(nTabela > 0, 'exemplo sem slide de tabela');
  node('scripts/captura.mjs', 'pagina', `${deck}#${nTabela}`, join(pasta, 'tabela.png'), '--seletor', '.slide.ativo table', '--largura', '1600', '--altura', '900', '--escala', '1');
  node('scripts/captura.mjs', 'video', deck, join(pasta, 'demo.webm'), '--roteiro', join(RAIZ, 'exemplos', 'roteiro.json'), '--largura', '960', '--altura', '540');
  py('scripts/gif.py', join(pasta, 'demo.webm'), join(pasta, 'demo.gif'), '--largura', '640');
  py('scripts/gif.py', join(pasta, 'demo.webm'), join(pasta, 'demo.mp4'));
  if (!existsSync(join(SAIDA, 'slides'))) exportacao();
  py('scripts/gif.py', '--de-imagens', join(SAIDA, 'slides', 'slide-0[1-3].png'), join(pasta, 'slides.gif'), '--segundos', '1', '--largura', '480');
  const cabeca = (f, n) => readFileSync(join(pasta, f)).subarray(0, n).toString('latin1');
  afirmar(cabeca('tabela.png', 8).slice(1, 4) === 'PNG', 'tabela.png inválido');
  afirmar(tamanho(join(pasta, 'demo.webm')) > 10_000, 'vídeo webm vazio');
  afirmar(cabeca('demo.gif', 6) === 'GIF89a', 'demo.gif inválido');
  afirmar(cabeca('slides.gif', 6) === 'GIF89a', 'slides.gif inválido');
  afirmar(cabeca('demo.mp4', 12).includes('ftyp'), 'demo.mp4 inválido');
  console.log('png por seletor, webm, gif de vídeo, mp4 e gif de imagens');
}

const PROIBIDO = [/os\.homedir\s*\(/, /expanduser\s*\(/, /Path\.home\s*\(/, /process\.env\.HOME\b/, /\$HOME\b/, /["'`\s]~\//];
function encontrar(texto) { return PROIBIDO.filter((re) => re.test(texto)).map(String); }

function home() {
  // Controle positivo: o detector precisa achar o padrão num texto que o contém.
  afirmar(encontrar("os.path.expanduser('~/x')").length > 0, 'detector não acusou o controle positivo');
  const arquivos = readdirSync(join(RAIZ, 'scripts')).filter((f) => /\.(mjs|py|sh)$/.test(f) && f !== 'autoteste.mjs');
  arquivos.push('../exemplos/figuras.py');
  for (const f of arquivos) {
    const achados = encontrar(readFileSync(join(RAIZ, 'scripts', f), 'utf8'));
    afirmar(achados.length === 0, `${f} referencia diretório do usuário: ${achados.join(', ')}`);
  }
  const amb = readFileSync(join(RAIZ, 'scripts', 'ambiente.sh'), 'utf8');
  for (const v of ['UV_CACHE_DIR', 'UV_PYTHON_INSTALL_DIR', 'npm_config_cache', 'PLAYWRIGHT_BROWSERS_PATH', 'MPLCONFIGDIR', 'XDG_CACHE_HOME', 'XDG_CONFIG_HOME']) {
    afirmar(new RegExp(`export ${v}="\\$_SKILL/\\.cache/`).test(amb), `ambiente.sh não fixa ${v} na skill`);
  }
  console.log(`${arquivos.length} scripts sem referência a diretório do usuário; 7 caches fixados na skill`);
}

const etapas = { estrutura, graficos, construcao, exportacao, midia, home };
const pedido = process.argv[2];
const lista = pedido === 'tudo' ? Object.keys(etapas) : [pedido];
for (const nome of lista) {
  if (!etapas[nome]) { console.error(`uso: autoteste.mjs ${Object.keys(etapas).join('|')}|tudo`); process.exit(2); }
  etapas[nome]();
  console.log(`AUTOTESTE ${nome} OK`);
}
