#!/usr/bin/env node
// Fase 2 (import automatizado): abre um Chromium visível, com um perfil
// persistente, para login manual no Penpot. Os cookies de sessão ficam
// gravados no próprio diretório de perfil (SQLite do Chrome) assim que o
// login é concluído — não depende de detectar a URL pós-login. O mesmo
// diretório de perfil é reaberto (headless) por import-svg-to-penpot.mjs.
// A senha nunca passa por este script nem é lida por ele.
import { chromium } from 'playwright';
import { mkdir, chmod, unlink } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { resolve } from 'node:path';
import { homedir } from 'node:os';

const DEFAULT_PROFILE_DIR = resolve(homedir(), '.config/mockup-lab/penpot-profile');

const PENPOT_HOST = 'penpot.lan';
const PENPOT_IP = '192.168.1.15';

function parseArgs(argv) {
  const args = { url: `http://${PENPOT_HOST}`, profileDir: DEFAULT_PROFILE_DIR };
  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === '--url') args.url = argv[++i];
    else if (arg === '--profile-dir') args.profileDir = resolve(argv[++i]);
    else throw new Error(`argumento desconhecido: ${arg}`);
  }
  return args;
}

async function chmodRecursive(path, mode) {
  await chmod(path, mode).catch(() => {});
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  const doneSignal = `${args.profileDir}.done`;
  await unlink(doneSignal).catch(() => {});

  await mkdir(args.profileDir, { recursive: true });
  await chmodRecursive(args.profileDir, 0o700);

  const context = await chromium.launchPersistentContext(args.profileDir, {
    headless: false,
    args: [`--host-resolver-rules=MAP ${PENPOT_HOST} ${PENPOT_IP}`],
  });
  const page = context.pages()[0] ?? (await context.newPage());
  await page.goto(args.url);

  console.log(`Janela aberta em ${args.url}. Faça login manualmente.`);
  console.log(`Quando terminar, sinalize criando o arquivo: ${doneSignal}`);
  console.log('(ex.: rode `touch ' + doneSignal + '` ou peça para o agente fazer isso)');
  console.log('Aguardando sinal (até 30 minutos)...');

  const deadline = Date.now() + 30 * 60 * 1000;
  while (!existsSync(doneSignal)) {
    if (Date.now() > deadline) {
      console.error('Tempo esgotado sem sinal de conclusão — fechando mesmo assim.');
      break;
    }
    await new Promise((r) => setTimeout(r, 2000));
  }
  await unlink(doneSignal).catch(() => {});

  await context.close();
  await chmodRecursive(args.profileDir, 0o700);

  console.log(`Perfil salvo em ${args.profileDir}.`);
  console.log('Trate este diretório como uma credencial: não versionar, não compartilhar.');
}

main().catch((err) => {
  console.error(`erro: ${err.message}`);
  process.exit(1);
});
