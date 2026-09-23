#!/usr/bin/env bash
# Caminho relativo: skills/stack/criar-app-tauri/scripts/checar-tauri.sh
#
# Gate de detecção da skill criar-app-tauri: confirma projeto Tauri 2 antes de escrever
# comando, plugin ou permissão.
#
#   checar-tauri.sh [--raiz <dir>]     (padrão: diretório corrente)
#
# Sai 0 se bate, 1 se diverge (inclusive Tauri 1), 2 se não achou o projeto.
set -euo pipefail

raiz="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --raiz) raiz="${2:?--raiz exige um diretório}"; shift 2 ;;
    -h|--help) sed -n '3,9p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) printf 'opção desconhecida: %s\n' "$1" >&2; exit 2 ;;
  esac
done

conf="$raiz/src-tauri/tauri.conf.json"
cargo="$raiz/src-tauri/Cargo.toml"
[[ -f "$conf" ]] || { printf 'sem %s — não é um projeto Tauri (veja definir-stack)\n' "$conf" >&2; exit 2; }
[[ -f "$cargo" ]] || { printf 'sem %s — projeto Tauri incompleto\n' "$cargo" >&2; exit 2; }

problemas=()

# Versão do crate tauri: aceita `tauri = "2..."` e `tauri = { version = "2..." }`.
linha_tauri="$(grep -E '^[[:space:]]*tauri[[:space:]]*=' "$cargo" | head -1 || true)"
versao="$(printf '%s' "$linha_tauri" | grep -oE '"[0-9]+(\.[0-9]+)*"' | head -1 | tr -d '"' || true)"
if [[ -z "$versao" ]]; then
  problemas+=("não consegui ler a versão do crate tauri em $cargo")
elif [[ "${versao%%.*}" != "2" ]]; then
  problemas+=("crate tauri $versao: esta skill é de Tauri 2 (a 1 usa allowlist, não capabilities)")
fi

# Tauri 1 deixa rastro no tauri.conf.json.
if grep -q '"allowlist"' "$conf"; then
  problemas+=("tauri.conf.json tem \"allowlist\": isto é Tauri 1")
fi

# capabilities/ é obrigatório em Tauri 2 — ausência costuma ser migração incompleta.
if [[ ! -d "$raiz/src-tauri/capabilities" ]]; then
  problemas+=("sem src-tauri/capabilities/: nenhuma permissão declarada (migração incompleta?)")
fi

# API do front, quando houver package.json.
pkg="$raiz/package.json"
api=""
if [[ -f "$pkg" ]] && command -v python3 >/dev/null 2>&1; then
  api="$(python3 - "$pkg" <<'PY'
import json, sys
try:
    p = json.load(open(sys.argv[1], encoding="utf-8"))
except (OSError, ValueError):
    sys.exit(0)
d = {**p.get("dependencies", {}), **p.get("devDependencies", {})}
print(d.get("@tauri-apps/api", ""))
PY
)"
  if [[ -n "$api" && "$(printf '%s' "$api" | grep -oE '[0-9]+' | head -1)" != "2" ]]; then
    problemas+=("@tauri-apps/api $api no front: incompatível com o crate 2.x")
  fi
fi

if (( ${#problemas[@]} )); then
  printf 'stack divergente — NÃO escreva comandos com esta skill:\n' >&2
  printf '  - %s\n' "${problemas[@]}" >&2
  printf '  → volte a definir-stack; migração de Tauri 1 para 2 é decisão (adr-writer).\n' >&2
  exit 1
fi

printf 'ok: tauri %s · capabilities presentes%s\n' "$versao" \
  "${api:+ · @tauri-apps/api $api}"
