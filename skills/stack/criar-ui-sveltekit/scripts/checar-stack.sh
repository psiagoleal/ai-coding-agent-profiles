#!/usr/bin/env bash
# Caminho relativo: skills/stack/criar-ui-sveltekit/scripts/checar-stack.sh
#
# Gate de detecção da skill criar-ui-sveltekit: confirma que o projeto é mesmo
# SvelteKit 2 + Svelte 5 antes de escrever qualquer componente.
#
#   checar-stack.sh [--raiz <dir>]     (padrão: diretório corrente)
#
# Sai 0 se bate, 1 se diverge, 2 se não achou manifesto. A saída é para ser lida e citada.
set -euo pipefail

raiz="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --raiz) raiz="${2:?--raiz exige um diretório}"; shift 2 ;;
    -h|--help) sed -n '3,9p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) printf 'opção desconhecida: %s\n' "$1" >&2; exit 2 ;;
  esac
done

pkg="$raiz/package.json"
[[ -f "$pkg" ]] || { printf 'sem %s — este não é um projeto Node/SvelteKit (veja definir-stack)\n' "$pkg" >&2; exit 2; }

python3 - "$pkg" <<'PY'
import json, re, sys

caminho = sys.argv[1]
try:
    pkg = json.load(open(caminho, encoding="utf-8"))
except (OSError, ValueError) as e:
    sys.exit(f"não consegui ler {caminho}: {e}")

deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}

def maior(spec):
    """Maior versão declarada no intervalo — '^5.0.0', '>=4 <6', '5.2.1' → 5."""
    achados = re.findall(r"(\d+)\.", spec or "")
    return int(achados[0]) if achados else None

problemas = []
kit = deps.get("@sveltejs/kit")
if kit is None:
    outro = next((n for n in ("react", "vue", "@angular/core", "solid-js") if n in deps), None)
    problemas.append("@sveltejs/kit ausente" + (f" — o projeto usa {outro}" if outro else ""))
elif (k := maior(kit)) is not None and k < 2:
    problemas.append(f"@sveltejs/kit {kit}: a skill assume SvelteKit 2 (rotas e actions mudaram)")
svelte = deps.get("svelte")
if svelte is None:
    problemas.append("svelte ausente")
elif (m := maior(svelte)) is not None and m < 5:
    problemas.append(f"svelte {svelte}: runes ($state/$props) exigem Svelte 5")

if problemas:
    print("stack divergente — NÃO escreva componentes com esta skill:", file=sys.stderr)
    for p in problemas:
        print(f"  - {p}", file=sys.stderr)
    print("  → volte a definir-stack e trate a divergência como decisão (adr-writer).", file=sys.stderr)
    raise SystemExit(1)

print(f"ok: @sveltejs/kit {deps['@sveltejs/kit']} · svelte {svelte}"
      + (f" · typescript {deps['typescript']}" if "typescript" in deps else " · SEM typescript (a skill assume TS)"))
PY
