#!/usr/bin/env node
// Captura de tela e gravação com Playwright usando o Chrome instalado.
//
// pagina <url|arquivo> <saida.png> [--seletor css] [--largura 1440] [--altura 900] [--escala 2]
//        [--pagina-inteira] [--esperar ms] [--destacar css] [--estado storage.json] [--ocultar css]
// video  <url|arquivo> <saida.webm> [--roteiro roteiro.json] [--largura 1280] [--altura 720] [--estado storage.json]
// deck   <deck.html> <pasta> [--pdf saida.pdf] [--tema nome] [--escala 1]
//
// roteiro.json: [{"acao":"ir","url":"..."}, {"acao":"clicar","seletor":"..."},
//   {"acao":"digitar","seletor":"...","texto":"..."}, {"acao":"rolar","y":600},
//   {"acao":"esperar","ms":800}, {"acao":"esperarSeletor","seletor":"..."}]
// Credencial nunca vai em argumento nem no roteiro: autentique uma vez e reuse o
// arquivo de --estado (storageState do Playwright), mantido fora do repositório.
import { existsSync, mkdirSync, readFileSync, renameSync, readdirSync, rmSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';
import { abrirNavegador, argumentos } from './comum.mjs';

function alvo(u) {
  if (/^[a-z]+:\/\//i.test(u)) return u;
  const caminho = resolve(u.split(/[?#]/)[0]);
  if (!existsSync(caminho)) throw new Error(`arquivo não encontrado: ${u}`);
  return pathToFileURL(caminho).href + (u.match(/[?#].*$/)?.[0] ?? '');
}

async function pagina(destino, saida, o) {
  const nav = await abrirNavegador();
  try {
    const ctx = await nav.newContext({
      viewport: { width: Number(o.largura ?? 1440), height: Number(o.altura ?? 900) },
      deviceScaleFactor: Number(o.escala ?? 2),
      storageState: o.estado,
    });
    const p = await ctx.newPage();
    await p.goto(alvo(destino), { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    if (o.esperar) await p.waitForTimeout(Number(o.esperar));
    if (o.ocultar) await p.addStyleTag({ content: `${o.ocultar}{visibility:hidden!important}` });
    if (o.destacar) {
      await p.addStyleTag({ content: `${o.destacar}{outline:4px solid #e4572e!important;outline-offset:4px!important}` });
    }
    mkdirSync(dirname(resolve(saida)), { recursive: true });
    if (o.seletor) await p.locator(o.seletor).first().screenshot({ path: saida, animations: 'disabled' });
    else await p.screenshot({ path: saida, fullPage: !!o['pagina-inteira'], animations: 'disabled' });
    console.log(`captura: ${resolve(saida)}`);
  } finally {
    await nav.close();
  }
}

async function video(destino, saida, o) {
  const largura = Number(o.largura ?? 1280);
  const altura = Number(o.altura ?? 720);
  const pasta = join(dirname(resolve(saida)), '.video-tmp');
  rmSync(pasta, { recursive: true, force: true });
  mkdirSync(pasta, { recursive: true });
  const roteiro = o.roteiro ? JSON.parse(readFileSync(o.roteiro, 'utf8')) : [{ acao: 'esperar', ms: 2000 }];
  const nav = await abrirNavegador();
  try {
    const ctx = await nav.newContext({
      viewport: { width: largura, height: altura },
      recordVideo: { dir: pasta, size: { width: largura, height: altura } },
      storageState: o.estado,
    });
    const p = await ctx.newPage();
    await p.goto(alvo(destino), { waitUntil: 'networkidle' });
    for (const passo of roteiro) {
      if (passo.acao === 'ir') await p.goto(alvo(passo.url), { waitUntil: 'networkidle' });
      else if (passo.acao === 'clicar') await p.locator(passo.seletor).first().click();
      else if (passo.acao === 'digitar') await p.locator(passo.seletor).first().pressSequentially(passo.texto, { delay: passo.atraso ?? 60 });
      else if (passo.acao === 'tecla') await p.keyboard.press(passo.tecla);
      else if (passo.acao === 'rolar') await p.mouse.wheel(0, passo.y ?? 600);
      else if (passo.acao === 'esperar') await p.waitForTimeout(passo.ms ?? 500);
      else if (passo.acao === 'esperarSeletor') await p.locator(passo.seletor).first().waitFor();
      else throw new Error(`ação desconhecida no roteiro: ${passo.acao}`);
    }
    await ctx.close(); // o vídeo só é gravado ao fechar o contexto
  } finally {
    await nav.close();
  }
  const gerado = readdirSync(pasta).find((f) => f.endsWith('.webm'));
  if (!gerado) throw new Error('Playwright não gerou o vídeo');
  mkdirSync(dirname(resolve(saida)), { recursive: true });
  renameSync(join(pasta, gerado), saida);
  rmSync(pasta, { recursive: true, force: true });
  console.log(`video: ${resolve(saida)}`);
}

async function deck(arquivo, pasta, o) {
  mkdirSync(pasta, { recursive: true });
  const nav = await abrirNavegador();
  try {
    const ctx = await nav.newContext({ viewport: { width: 1600, height: 900 }, deviceScaleFactor: Number(o.escala ?? 1) });
    const p = await ctx.newPage();
    const tema = o.tema ? `?tema=${encodeURIComponent(o.tema)}` : '';
    await p.goto(alvo(arquivo) + tema, { waitUntil: 'networkidle' });
    await p.evaluate(() => document.fonts.ready);
    const total = await p.evaluate(() => window.deck?.total ?? 0);
    if (!total) throw new Error('o arquivo não expõe window.deck: use o template da skill');
    await p.addStyleTag({ content: '.controles,.hud{display:none!important}' });
    for (let i = 0; i < total; i += 1) {
      await p.evaluate((n) => window.deck.mostrar(n, true), i);
      const destino = join(pasta, `slide-${String(i + 1).padStart(2, '0')}.png`);
      await p.locator('.slide.ativo').screenshot({ path: destino, animations: 'disabled' });
    }
    console.log(`slides: ${total} PNG em ${resolve(pasta)}`);
    if (o.pdf) {
      await p.emulateMedia({ media: 'print' });
      await p.pdf({ path: o.pdf, preferCSSPageSize: true, printBackground: true });
      console.log(`pdf: ${resolve(o.pdf)}`);
    }
  } finally {
    await nav.close();
  }
}

async function main() {
  const [modo, ...resto] = process.argv.slice(2);
  const { posicionais, opcoes } = argumentos(resto, ['pagina-inteira']);
  const [a, b] = posicionais;
  if (!modo || !a || !b) {
    console.error('uso: captura.mjs pagina|video|deck <origem> <saida> [opções]  (ver cabeçalho do arquivo)');
    process.exit(2);
  }
  if (modo === 'pagina') await pagina(a, b, opcoes);
  else if (modo === 'video') await video(a, b, opcoes);
  else if (modo === 'deck') await deck(a, b, opcoes);
  else throw new Error(`modo desconhecido: ${modo}`);
}

main().catch((e) => { console.error(`ERRO ${e.message}`); process.exit(1); });
