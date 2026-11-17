#!/usr/bin/env node
// Constrói o deck autocontido: aplica temas, renderiza Mermaid e LaTeX em SVG,
// embute fontes e todos os recursos locais. O resultado é um único .html que
// abre sem rede.
//
// uso: node construir.mjs fonte.html saida.html [--temas tecnico,auditorio] [--tema tecnico]
//                         [--sem-fontes] [--estrito] [--max-mb 15]
import { existsSync, readFileSync, writeFileSync, statSync } from 'node:fs';
import { dirname, extname, join, resolve } from 'node:path';
import { MODULOS, abrirNavegador, argumentos, carregarTemas, cssDosTemas, fontFaces } from './comum.mjs';

const MIME = {
  '.svg': 'image/svg+xml', '.png': 'image/png', '.jpg': 'image/jpeg', '.jpeg': 'image/jpeg',
  '.gif': 'image/gif', '.webp': 'image/webp', '.avif': 'image/avif', '.mp4': 'video/mp4',
  '.webm': 'video/webm', '.woff2': 'font/woff2', '.woff': 'font/woff', '.ttf': 'font/ttf',
  '.css': 'text/css', '.js': 'text/javascript', '.json': 'application/json',
};
const MARCA = /\/\* TEMAS:inicio \*\/[\s\S]*?\/\* TEMAS:fim \*\//;

function desescapar(texto) {
  return texto
    .replace(/&lt;/g, '<').replace(/&gt;/g, '>').replace(/&quot;/g, '"')
    .replace(/&#39;/g, "'").replace(/&nbsp;/g, ' ').replace(/&amp;/g, '&');
}
const remoto = (u) => /^(https?:)?\/\//i.test(u);
const especial = (u) => /^(data:|blob:|#|mailto:|tel:|javascript:)/i.test(u);

function dataUri(caminho) {
  const tipo = MIME[extname(caminho).toLowerCase()] ?? 'application/octet-stream';
  return `data:${tipo};base64,${readFileSync(caminho).toString('base64')}`;
}

function inlinarUrlsCss(css, base, relatorio) {
  return css.replace(/url\(\s*(['"]?)([^'")]+)\1\s*\)/g, (todo, _q, url) => {
    if (especial(url)) return todo;
    if (remoto(url)) { relatorio.externos.add(url); return todo; }
    const alvo = resolve(base, url.split(/[?#]/)[0]);
    if (!existsSync(alvo)) { relatorio.faltando.add(url); return todo; }
    relatorio.recursos += 1;
    return `url(${dataUri(alvo)})`;
  });
}

// <img src="x.svg" data-inline>: o SVG entra no HTML (não como data URI) com ids
// prefixados e cores do tema trocadas por variáveis, para seguir a troca de tema.
function inlinarSvgs(html, base, tema, relatorio) {
  let n = 0;
  return html.replace(/<img\b[^>]*\bdata-inline\b[^>]*>/gi, (tag) => {
    const src = tag.match(/\bsrc=["']([^"']+)["']/i)?.[1];
    if (!src || !src.toLowerCase().endsWith('.svg') || remoto(src)) return tag;
    const alvo = resolve(base, src);
    if (!existsSync(alvo)) { relatorio.faltando.add(src); return tag; }
    n += 1;
    const prefixo = `svg${n}-`;
    const alt = tag.match(/\balt=["']([^"']*)["']/i)?.[1] ?? '';
    const classe = tag.match(/\bclass=["']([^"']*)["']/i)?.[1];
    let svg = readFileSync(alvo, 'utf8')
      .replace(/<\?xml[\s\S]*?\?>/g, '').replace(/<!DOCTYPE[\s\S]*?>/gi, '').replace(/<!--[\s\S]*?-->/g, '').trim();
    svg = svg
      .replace(/\bid="([^"]+)"/g, (_t, id) => `id="${prefixo}${id}"`)
      .replace(/url\(#([^)]+)\)/g, (_t, id) => `url(#${prefixo}${id})`)
      .replace(/\b(xlink:href|href)="#([^"]+)"/g, (_t, a, id) => `${a}="#${prefixo}${id}"`);
    // data-inline="monocromatico": arte em preto (TikZ, Graphviz, PlantUML) passa a usar
    // a cor do texto do tema, para continuar legível no tema escuro.
    const mono = /\bdata-inline=["']monocromatico["']/i.test(tag);
    if (mono) {
      svg = svg
        .replace(/(fill|stroke)=(["'])(#000000|#000|black)\2/gi, (_t, a, q) => `${a}=${q}currentColor${q}`)
        .replace(/(fill|stroke):\s*(#000000|#000|black)\b/gi, (_t, a) => `${a}:currentColor`);
    }
    const extra = mono ? ' fill="currentColor" style="color:var(--texto)"' : '';
    svg = svg.replace(/<svg\b/, `<svg role="img" aria-label="${alt}"${classe ? ` class="${classe}"` : ''}${extra}`);
    relatorio.recursos += 1;
    relatorio.svgInline += 1;
    return temarSvg(svg, tema);
  });
}

function inlinarRecursos(html, base, relatorio) {
  // <link rel="stylesheet" href="...">
  html = html.replace(/<link\b[^>]*>/gi, (tag) => {
    if (!/rel=["']?stylesheet/i.test(tag)) return tag;
    const href = tag.match(/href=["']([^"']+)["']/i)?.[1];
    if (!href || especial(href)) return tag;
    if (remoto(href)) { relatorio.externos.add(href); return tag; }
    const alvo = resolve(base, href);
    if (!existsSync(alvo)) { relatorio.faltando.add(href); return tag; }
    relatorio.recursos += 1;
    return `<style>\n${inlinarUrlsCss(readFileSync(alvo, 'utf8'), dirname(alvo), relatorio)}\n</style>`;
  });
  // <script src="..."></script>
  html = html.replace(/<script\b([^>]*)\bsrc=["']([^"']+)["']([^>]*)>\s*<\/script>/gi, (tag, a, src, b) => {
    if (remoto(src)) { relatorio.externos.add(src); return tag; }
    const alvo = resolve(base, src);
    if (!existsSync(alvo)) { relatorio.faltando.add(src); return tag; }
    relatorio.recursos += 1;
    const codigo = readFileSync(alvo, 'utf8').replace(/<\/script/gi, '<\\/script');
    return `<script${a}${b}>\n${codigo}\n</script>`;
  });
  // src/poster em img, source, video, audio
  html = html.replace(/<(img|source|video|audio)\b[^>]*>/gi, (tag) =>
    tag.replace(/\b(src|poster)=["']([^"']+)["']/gi, (attr, nome, url) => {
      if (especial(url)) return attr;
      if (remoto(url)) { relatorio.externos.add(url); return attr; }
      const alvo = resolve(base, url);
      if (!existsSync(alvo)) { relatorio.faltando.add(url); return attr; }
      relatorio.recursos += 1;
      if (statSync(alvo).size > 5 * 1024 * 1024) relatorio.avisos.push(`${url} tem mais de 5 MB; reduza (gif.py --formato mp4)`);
      return `${nome}="${dataUri(alvo)}"`;
    }),
  );
  // url() em <style> e em style="..."
  html = html.replace(/(<style\b[^>]*>)([\s\S]*?)(<\/style>)/gi, (_t, a, css, b) => a + inlinarUrlsCss(css, base, relatorio) + b);
  html = html.replace(/\bstyle="([^"]*url\([^"]*)"/gi, (_t, css) => `style="${inlinarUrlsCss(css, base, relatorio)}"`);
  // <link rel="icon"> e similares remotos: só reportar
  for (const m of html.matchAll(/<(?:link|iframe|object|embed)\b[^>]*(?:href|src|data)=["'](https?:)?\/\/[^"']+["']/gi)) {
    relatorio.externos.add(m[0].slice(0, 120));
  }
  return html;
}

const TOKENS_MERMAID = ['fundo', 'superficie', 'texto', 'suave', 'linha', 'primaria', 'primaria-suave', 'enfase'];

function variaveisMermaid(tema) {
  const c = tema.cores;
  return {
    background: c.fundo, mainBkg: c['primaria-suave'], primaryColor: c['primaria-suave'],
    primaryBorderColor: c.primaria, primaryTextColor: c.texto, nodeBorder: c.primaria,
    secondaryColor: c.superficie, secondaryBorderColor: c.suave, secondaryTextColor: c.texto,
    tertiaryColor: c.superficie, tertiaryBorderColor: c.linha, tertiaryTextColor: c.texto,
    lineColor: c.suave, textColor: c.texto, titleColor: c.texto,
    clusterBkg: c.superficie, clusterBorder: c.linha, edgeLabelBackground: c.fundo,
    noteBkgColor: c.superficie, noteBorderColor: c.enfase, noteTextColor: c.texto,
    actorBkg: c['primaria-suave'], actorBorder: c.primaria, actorTextColor: c.texto,
    signalColor: c.suave, signalTextColor: c.texto, labelBoxBkgColor: c.superficie,
    fontFamily: `"${tema.fontes.texto}", sans-serif`, fontSize: '22px',
  };
}

// Troca as cores literais do tema-base por var(--token, cor) para o diagrama
// acompanhar a troca de tema na apresentação.
function temarSvg(svg, tema) {
  const pares = TOKENS_MERMAID.map((t) => [tema.cores[t].toLowerCase(), t]);
  const vistos = new Set();
  for (const [cor, token] of pares) {
    if (vistos.has(cor)) continue;
    vistos.add(cor);
    const re = new RegExp(cor, 'gi');
    svg = svg.replace(re, `var(--${token}, ${cor})`);
  }
  // Atributos de apresentação SVG (fill="...") não aceitam var(); só o CSS aceita.
  svg = svg.replace(/\b(fill|stroke|stop-color)="var\((--[\w-]+), (#[0-9a-f]{3,8})\)"/gi, (_t, attr, tok, cor) => `style="${attr}:var(${tok}, ${cor})"`);
  return svg;
}

async function renderizar(html, tema, fontesCss) {
  const mermaids = [...html.matchAll(/<pre\b[^>]*class=["'][^"']*\bmermaid\b[^"']*["'][^>]*>([\s\S]*?)<\/pre>/gi)];
  const texs = [...html.matchAll(/<(span|div)\b([^>]*)class=["'](tex|tex-bloco)(\s[^"']*)?["']([^>]*)>([\s\S]*?)<\/\1>/gi)];
  if (!mermaids.length && !texs.length) return { html, mermaid: 0, tex: 0 };

  const navegador = await abrirNavegador();
  try {
    const pagina = await navegador.newPage();
    await pagina.setContent(`<!doctype html><html><head><meta charset="utf-8"><style>${fontesCss}
      body{font-family:"${tema.fontes.texto}",sans-serif;color:${tema.cores.texto};background:${tema.cores.fundo}}</style></head><body></body></html>`);
    await pagina.evaluate(() => document.fonts.ready);
    const erros = [];
    let saida = html;

    if (mermaids.length) {
      await pagina.addScriptTag({ path: join(MODULOS, 'mermaid', 'dist', 'mermaid.min.js') });
      const vars = variaveisMermaid(tema);
      await pagina.evaluate((v) => {
        window.mermaid.initialize({ startOnLoad: false, theme: 'base', themeVariables: v, securityLevel: 'strict', flowchart: { htmlLabels: false, curve: 'basis' } });
      }, vars);
      let n = 0;
      for (const m of mermaids) {
        n += 1;
        const fonte = desescapar(m[1]).trim();
        const resultado = await pagina.evaluate(async ({ id, fonte }) => {
          try { return { svg: (await window.mermaid.render(id, fonte)).svg }; } catch (e) { return { erro: String(e.message || e) }; }
        }, { id: `mmd-${n}`, fonte });
        if (resultado.erro) { erros.push(`Mermaid ${n}: ${resultado.erro.split('\n')[0]}`); continue; }
        const titulo = m[0].match(/data-titulo=["']([^"']+)["']/)?.[1] ?? 'Diagrama';
        saida = saida.replace(m[0], `<div class="diagrama" role="img" aria-label="${titulo}">${temarSvg(resultado.svg, tema)}</div>`);
      }
    }

    if (texs.length) {
      await pagina.evaluate(() => {
        window.MathJax = { svg: { fontCache: 'none' }, startup: { typeset: false } };
      });
      await pagina.addScriptTag({ path: join(MODULOS, 'mathjax', 'es5', 'tex-svg-full.js') });
      await pagina.evaluate(() => window.MathJax.startup.promise);
      for (const m of texs) {
        const [todo, tag, antes, classe, extra = '', depois, conteudo] = m;
        const tex = desescapar(conteudo).trim();
        const r = await pagina.evaluate(({ tex, bloco }) => {
          try {
            const no = window.MathJax.tex2svg(tex, { display: bloco });
            const svg = no.querySelector('svg');
            const erro = no.querySelector('[data-mjx-error]');
            if (erro) return { erro: erro.getAttribute('data-mjx-error') };
            svg.setAttribute('role', 'img');
            svg.setAttribute('aria-label', tex);
            return { svg: svg.outerHTML };
          } catch (e) { return { erro: String(e.message || e) }; }
        }, { tex, bloco: classe === 'tex-bloco' });
        if (r.erro) { erros.push(`LaTeX "${tex.slice(0, 40)}": ${r.erro}`); continue; }
        saida = saida.replace(todo, `<${tag}${antes}class="${classe}${extra}"${depois}>${r.svg}</${tag}>`);
      }
    }
    if (erros.length) throw new Error(`falha ao renderizar:\n  ${erros.join('\n  ')}`);
    return { html: saida, mermaid: mermaids.length, tex: texs.length };
  } finally {
    await navegador.close();
  }
}

async function main() {
  const { posicionais, opcoes } = argumentos(process.argv.slice(2), ['sem-fontes', 'estrito']);
  const [entrada, saida] = posicionais;
  if (!entrada || !saida) {
    console.error('uso: construir.mjs fonte.html saida.html [--temas a,b] [--tema a] [--sem-fontes] [--estrito] [--max-mb 15]');
    process.exit(2);
  }
  const temas = carregarTemas();
  const nomes = opcoes.temas ? opcoes.temas.split(',') : Object.keys(temas);
  for (const n of nomes) if (!temas[n]) throw new Error(`tema desconhecido: ${n}`);
  let html = readFileSync(entrada, 'utf8');
  const base = dirname(resolve(entrada));
  const relatorio = { recursos: 0, svgInline: 0, externos: new Set(), faltando: new Set(), avisos: [] };

  if (!MARCA.test(html)) throw new Error('fonte sem o bloco /* TEMAS:inicio */ ... /* TEMAS:fim */ (use templates/deck.html)');
  html = html.replace(MARCA, () => cssDosTemas(nomes));
  const padrao = opcoes.tema ?? html.match(/data-tema="([^"]+)"/)?.[1] ?? nomes[0];
  const inicial = nomes.includes(padrao) ? padrao : nomes[0];
  html = html.replace(/<html\b[^>]*>/i, (tag) => {
    let t = tag.replace(/\sdata-temas="[^"]*"/, '').replace(/\sdata-tema="[^"]*"/, '');
    return t.replace(/>$/, ` data-tema="${inicial}" data-temas="${nomes.join(',')}">`);
  });

  const fontes = opcoes['sem-fontes'] ? { css: '', faltando: [], bytes: 0, arquivos: 0 } : fontFaces(temas, nomes);
  const render = await renderizar(html, temas[inicial], fontes.css);
  html = render.html;
  if (fontes.css) html = html.replace(/<\/head>/i, `<style>/* fontes embutidas */\n${fontes.css}\n</style>\n</head>`);
  html = inlinarSvgs(html, base, temas[inicial], relatorio);
  html = inlinarRecursos(html, base, relatorio);

  writeFileSync(saida, html, 'utf8');
  const mb = Buffer.byteLength(html) / 1024 / 1024;
  console.log(`saida: ${resolve(saida)}`);
  console.log(`tamanho: ${mb.toFixed(2)} MB | temas: ${nomes.join(',')} (inicial ${inicial})`);
  console.log(`mermaid: ${render.mermaid} | latex: ${render.tex} | svg inline: ${relatorio.svgInline} | recursos embutidos: ${relatorio.recursos} | fontes: ${fontes.arquivos} (${(fontes.bytes / 1024).toFixed(0)} KB)`);
  for (const f of fontes.faltando) console.log(`AVISO fonte não encontrada em node_modules/@fontsource, usa a reserva: ${f}`);
  for (const a of relatorio.avisos) console.log(`AVISO ${a}`);
  for (const f of relatorio.faltando) console.log(`ERRO recurso local não encontrado: ${f}`);
  for (const e of relatorio.externos) console.log(`EXTERNO ${e}`);
  const limite = Number(opcoes['max-mb'] ?? 15);
  let ok = relatorio.faltando.size === 0;
  if (mb > limite) { console.log(`ERRO arquivo acima de ${limite} MB`); ok = false; }
  if (opcoes.estrito && relatorio.externos.size) { console.log('ERRO --estrito: há recursos externos'); ok = false; }
  if (!ok) process.exit(1);
  console.log('CONSTRUCAO OK');
}

main().catch((e) => { console.error(`ERRO ${e.message}`); process.exit(1); });

