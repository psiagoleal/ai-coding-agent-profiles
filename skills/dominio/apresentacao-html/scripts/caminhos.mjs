// Importado antes do playwright-core: fixa o diretório de binários do Playwright
// (ffmpeg da gravação de vídeo) dentro da skill, nunca no cache do usuário.
import { dirname, join, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';

const raiz = resolve(dirname(fileURLToPath(import.meta.url)), '..');
process.env.PLAYWRIGHT_BROWSERS_PATH ??= join(raiz, '.cache', 'ms-playwright');
