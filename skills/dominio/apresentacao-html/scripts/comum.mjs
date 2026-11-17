// Utilidades compartilhadas pelos scripts Node da skill.
import './caminhos.mjs';
import { chromium } from 'playwright-core';
import { existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { execFileSync } from 'node:child_process';

export const RAIZ = resolve(dirname(fileURLToPath(import.meta.url)), '..');
export const MODULOS = join(RAIZ, 'node_modules');
export const CACHE = join(RAIZ, '.cache');

// Caches e configuração de navegador ficam dentro da skill (ADR 0011 do acervo:
// nada em diretório do usuário).
export function ambienteLocal() {
  const xdgCache = join(CACHE, 'xdg-cache');
  const xdgConfig = join(CACHE, 'xdg-config');
  for (const d of [xdgCache, xdgConfig]) mkdirSync(d, { recursive: true });
  return { ...process.env, XDG_CACHE_HOME: xdgCache, XDG_CONFIG_HOME: xdgConfig };
}

export async function abrirNavegador() {
  const opcoes = {
    args: ['--no-sandbox', '--disable-gpu', '--disable-dev-shm-usage', '--font-render-hinting=none'],
    env: ambienteLocal(),
  };
  if (process.env.CHROME_PATH) opcoes.executablePath = process.env.CHROME_PATH;
  else opcoes.channel = 'chrome';
  try {
    return await chromium.launch(opcoes);
  } catch (erro) {
    throw new Error(
      `não abri o Chrome (${erro.message.split('\n')[0]}). Instale o Google Chrome ou aponte CHROME_PATH para um Chromium.`,
    );
  }
}

export function carregarTemas() {
  return JSON.parse(readFileSync(join(RAIZ, 'temas.json'), 'utf8')).temas;
}

export function cssDosTemas(nomes) {
  const args = [join(RAIZ, 'scripts', 'tema.py'), 'css'];
  if (nomes?.length) args.push('--temas', nomes.join(','));
  return execFileSync('python3', ['-I', ...args], { encoding: 'utf8' }).trim();
}

// Pesos embutidos por papel tipográfico. Só subconjunto latin (cobre o português).
const PESOS = { titulo: [600, 700], texto: [400, 600], mono: [400, 500] };

export function fontFaces(temas, nomes) {
  const pedidos = new Map();
  for (const nome of nomes) {
    for (const [papel, familia] of Object.entries(temas[nome].fontes)) {
      const pesos = pedidos.get(familia) ?? new Set();
      for (const p of PESOS[papel] ?? [400]) pesos.add(p);
      pedidos.set(familia, pesos);
    }
  }
  const regras = [];
  const faltando = [];
  let bytes = 0;
  for (const [familia, pesos] of pedidos) {
    const slug = familia.toLowerCase().replace(/\s+/g, '-');
    for (const peso of [...pesos].sort()) {
      const arquivo = join(MODULOS, '@fontsource', slug, 'files', `${slug}-latin-${peso}-normal.woff2`);
      if (!existsSync(arquivo)) {
        faltando.push(`${familia} ${peso}`);
        continue;
      }
      const dados = readFileSync(arquivo);
      bytes += dados.length;
      regras.push(
        `@font-face{font-family:"${familia}";font-style:normal;font-weight:${peso};font-display:swap;` +
          `src:url(data:font/woff2;base64,${dados.toString('base64')}) format("woff2");}`,
      );
    }
  }
  return { css: regras.join('\n'), faltando, bytes, arquivos: regras.length };
}

export function argumentos(argv, opcoesBooleanas = []) {
  const posicionais = [];
  const opcoes = {};
  for (let i = 0; i < argv.length; i += 1) {
    const a = argv[i];
    if (a.startsWith('--')) {
      const chave = a.slice(2);
      if (opcoesBooleanas.includes(chave)) opcoes[chave] = true;
      else opcoes[chave] = argv[++i];
    } else posicionais.push(a);
  }
  return { posicionais, opcoes };
}
