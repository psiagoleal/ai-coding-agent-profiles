#!/usr/bin/env node
// Fase 2: serializa uma variante HTML aprovada em SVG importável no Penpot,
// usando dom-to-svg (https://github.com/felixfbecker/dom-to-svg) carregado
// em tempo de execução via esm.sh dentro do próprio contexto do browser.
// Requer acesso à internet no momento do export (não precisa estar instalado
// localmente).
import { chromium } from 'playwright';
import { mkdir, writeFile } from 'node:fs/promises';
import { resolve, dirname } from 'node:path';
import { pathToFileURL } from 'node:url';

const DOM_TO_SVG_CDN = 'https://esm.sh/dom-to-svg@0.12.2';

function parseArgs(argv) {
  const args = { viewport: '1440x900' };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--input') args.input = argv[++i];
    else if (arg === '--output') args.output = argv[++i];
    else if (arg === '--viewport') args.viewport = argv[++i];
    else throw new Error(`argumento desconhecido: ${arg}`);
  }
  if (!args.input || !args.output) {
    throw new Error('uso: export-svg-for-penpot.mjs --input <arquivo.html> --output <arquivo.svg> [--viewport 1440x900]');
  }
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const inputPath = resolve(args.input);
  const outputPath = resolve(args.output);
  const [width, height] = args.viewport.split('x').map(Number);
  if (!width || !height) throw new Error(`viewport inválido: "${args.viewport}"`);

  await mkdir(dirname(outputPath), { recursive: true });

  const browser = await chromium.launch();
  const page = await browser.newPage();

  try {
    await page.setViewportSize({ width, height });
    await page.goto(pathToFileURL(inputPath).href, { waitUntil: 'networkidle' });

    await page.addScriptTag({
      type: 'module',
      content: `
        import { documentToSVG, inlineResources } from '${DOM_TO_SVG_CDN}';
        window.__domToSvg = { documentToSVG, inlineResources };
      `,
    });
    await page.waitForFunction(() => window.__domToSvg !== undefined);

    const svgString = await page.evaluate(async () => {
      const { documentToSVG, inlineResources } = window.__domToSvg;
      const svgDocument = documentToSVG(document);
      await inlineResources(svgDocument.documentElement);
      return new XMLSerializer().serializeToString(svgDocument);
    });

    await writeFile(outputPath, svgString, 'utf8');
  } finally {
    await browser.close();
  }

  console.log(`SVG exportado em ${outputPath}`);
  console.log('Confira visualmente contra o screenshot da Fase 1 antes de importar no Penpot');
  console.log('(File -> Import, ou arraste o arquivo para o canvas).');
}

main().catch((err) => {
  console.error(`erro: ${err.message}`);
  process.exit(1);
});
