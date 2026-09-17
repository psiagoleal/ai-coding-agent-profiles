#!/usr/bin/env node
// Fase 2 (import automatizado): abre uma sessão autenticada (perfil salvo por
// penpot-login.mjs), cria um novo arquivo em "Drafts" (ou no projeto indicado
// se já existir), renomeia e "cola" o SVG exportado como camadas nativas
// editáveis, via um evento paste sintético — o mesmo mecanismo que o Penpot
// usa quando você copia/cola código SVG manualmente no canvas.
import { chromium } from 'playwright';
import { readFile } from 'node:fs/promises';
import { resolve, basename, extname } from 'node:path';
import { homedir } from 'node:os';

const DEFAULT_PROFILE_DIR = resolve(homedir(), '.config/mockup-lab/penpot-profile');
const PENPOT_HOST = 'penpot.lan';
const PENPOT_IP = '192.168.1.15';

function parseArgs(argv) {
  const args = {
    url: `http://${PENPOT_HOST}`,
    profileDir: DEFAULT_PROFILE_DIR,
    project: 'Drafts',
  };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--svg') args.svg = resolve(argv[++i]);
    else if (arg === '--file-name') args.fileName = argv[++i];
    else if (arg === '--project') args.project = argv[++i];
    else if (arg === '--url') args.url = argv[++i];
    else if (arg === '--profile-dir') args.profileDir = resolve(argv[++i]);
    else throw new Error(`argumento desconhecido: ${arg}`);
  }
  if (!args.svg) {
    throw new Error('uso: import-svg-to-penpot.mjs --svg <arquivo.svg> [--file-name nome] [--project "Drafts"]');
  }
  if (!args.fileName) args.fileName = basename(args.svg, extname(args.svg));
  return args;
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const svgContent = await readFile(args.svg, 'utf8');

  const context = await chromium.launchPersistentContext(args.profileDir, {
    headless: true,
    viewport: { width: 1280, height: 800 },
    args: [`--host-resolver-rules=MAP ${PENPOT_HOST} ${PENPOT_IP}`],
  });

  try {
    const page = context.pages()[0] ?? (await context.newPage());
    await page.goto(args.url, { waitUntil: 'networkidle' });

    if (page.url().includes('/auth/login')) {
      throw new Error(
        `sessão não autenticada (caiu na tela de login). Rode penpot-login.mjs --profile-dir "${args.profileDir}" de novo.`,
      );
    }

    await page.getByText(args.project, { exact: true }).first().click();
    await page.waitForTimeout(1000);

    await page.getByText(/new file/i).click();
    await page.waitForURL(/#\/workspace\?/, { timeout: 15000 });
    await page.waitForTimeout(1500);

    const fileNameLabel = page.getByText('New File', { exact: false }).first();
    await fileNameLabel.dblclick();
    await page.keyboard.press('Control+A');
    await page.keyboard.type(args.fileName);
    await page.keyboard.press('Enter');
    await page.waitForTimeout(1000);

    await page.mouse.click(640, 400);
    await page.waitForTimeout(300);
    await page.evaluate((svgText) => {
      const dataTransfer = new DataTransfer();
      dataTransfer.setData('text/plain', svgText);
      const event = new ClipboardEvent('paste', {
        clipboardData: dataTransfer,
        bubbles: true,
        cancelable: true,
      });
      document.dispatchEvent(event);
    }, svgContent);

    await page.getByText('svg', { exact: true }).first().waitFor({ timeout: 10000 });
    // Penpot sincroniza a mudança para o backend via websocket de forma
    // assíncrona/debounced; fechar o browser cedo demais aqui perde a
    // alteração antes dela ser persistida. Dar folga generosa antes de fechar.
    await page.waitForTimeout(4000);

    console.log(`Importado em: ${page.url()}`);
    console.log('Confira visualmente o arquivo no Penpot antes de considerar pronto.');
  } finally {
    await context.close();
  }
}

main().catch((err) => {
  console.error(`erro: ${err.message}`);
  process.exit(1);
});
