#!/usr/bin/env node
// Fase 1: renderiza cada variante HTML em N viewports para PNGs comparáveis.
import { chromium } from 'playwright';
import { readdir, mkdir } from 'node:fs/promises';
import { resolve, join, basename, extname } from 'node:path';
import { pathToFileURL } from 'node:url';

function parseArgs(argv) {
  const args = { viewports: '1440x900' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--input') args.input = argv[++i];
    else if (arg === '--output') args.output = argv[++i];
    else if (arg === '--viewports') args.viewports = argv[++i];
    else throw new Error(`argumento desconhecido: ${arg}`);
  }
  if (!args.input || !args.output) {
    throw new Error('uso: render-variants.mjs --input <dir> --output <dir> [--viewports 1440x900,390x844]');
  }
  return args;
}

function parseViewports(spec) {
  return spec.split(',').map((part) => {
    const [w, h] = part.trim().split('x').map(Number);
    if (!w || !h) throw new Error(`viewport inválido: "${part}" (esperado ex. 1440x900)`);
    return { width: w, height: h };
  });
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inputDir = resolve(args.input);
  const outputDir = resolve(args.output);
  const viewports = parseViewports(args.viewports);

  const entries = await readdir(inputDir);
  const htmlFiles = entries.filter((f) => extname(f).toLowerCase() === '.html').sort();
  if (htmlFiles.length === 0) {
    throw new Error(`nenhum .html encontrado em ${inputDir}`);
  }

  await mkdir(outputDir, { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage();
  const generated = [];

  try {
    for (const file of htmlFiles) {
      const slug = basename(file, extname(file));
      const url = pathToFileURL(join(inputDir, file)).href;
      for (const { width, height } of viewports) {
        await page.setViewportSize({ width, height });
        await page.goto(url, { waitUntil: 'networkidle' });
        const outPath = join(outputDir, `${slug}__${width}x${height}.png`);
        await page.screenshot({ path: outPath, fullPage: true });
        generated.push(outPath);
      }
    }
  } finally {
    await browser.close();
  }

  console.log(`Renderizado(s) ${generated.length} PNG(s) em ${outputDir}:`);
  for (const path of generated) console.log(`  - ${path}`);
}

main().catch((err) => {
  console.error(`erro: ${err.message}`);
  process.exit(1);
});
