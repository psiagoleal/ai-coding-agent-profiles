#!/usr/bin/env bash
# Caminho relativo: skills/stack/criar-servico-fastapi/scripts/checar-stack.sh
#
# Gate de detecção da skill criar-servico-fastapi: confirma FastAPI e Pydantic v2 antes
# de escrever rota, dependência ou modelo.
#
#   checar-stack.sh [--raiz <dir>]     (padrão: diretório corrente)
#
# Sai 0 se bate, 1 se diverge (ex.: Pydantic v1), 2 se não achou manifesto Python.
set -euo pipefail

raiz="."
while [[ $# -gt 0 ]]; do
  case "$1" in
    --raiz) raiz="${2:?--raiz exige um diretório}"; shift 2 ;;
    -h|--help) sed -n '3,9p' "$0" | sed 's/^# \?//'; exit 0 ;;
    *) printf 'opção desconhecida: %s\n' "$1" >&2; exit 2 ;;
  esac
done

manifesto=""
for cand in pyproject.toml requirements.txt; do
  [[ -f "$raiz/$cand" ]] && { manifesto="$raiz/$cand"; break; }
done
[[ -n "$manifesto" ]] || {
  printf 'sem pyproject.toml nem requirements.txt em %s — não é projeto Python (veja definir-stack)\n' "$raiz" >&2
  exit 2
}

python3 - "$manifesto" "$raiz" <<'PY'
import re, sys, tomllib
from pathlib import Path

manifesto, raiz = Path(sys.argv[1]), Path(sys.argv[2])
deps: list[str] = []
if manifesto.name == "pyproject.toml":
    try:
        d = tomllib.loads(manifesto.read_text(encoding="utf-8"))
    except (OSError, tomllib.TOMLDecodeError) as e:
        sys.exit(f"não consegui ler {manifesto}: {e}")
    proj = d.get("project", {})
    deps += proj.get("dependencies", []) or []
    for extra in (proj.get("optional-dependencies") or {}).values():
        deps += extra
    poesia = d.get("tool", {}).get("poetry", {}).get("dependencies", {})
    deps += [f"{k}{v if isinstance(v, str) else ''}" for k, v in poesia.items()]
else:
    deps += [l.strip() for l in manifesto.read_text(encoding="utf-8").splitlines()
             if l.strip() and not l.lstrip().startswith("#")]

def achar(nome: str) -> str | None:
    p = re.compile(rf"^{nome}\b", re.I)
    return next((d for d in deps if p.match(d.strip())), None)

problemas, notas = [], []

if not achar("fastapi"):
    outro = next((n for n in ("django", "flask", "litestar", "aiohttp") if achar(n)), None)
    problemas.append("fastapi ausente" + (f" — o projeto usa {outro}" if outro else ""))

pyd = achar("pydantic")
if pyd is None:
    notas.append("pydantic não declarado (vem junto do fastapi; a v2 é a assumida aqui)")
else:
    m = re.search(r"(\d+)", pyd.split(";")[0].replace("pydantic", ""))
    if m and int(m.group(1)) < 2:
        problemas.append(f"{pyd.strip()}: esta skill assume Pydantic v2 (a v1 usa @validator e .dict())")

# Sinal de rota async com cliente bloqueante — não reprova, mas vale dizer.
if achar("requests") and any((raiz / "src").rglob("*.py") if (raiz / "src").is_dir() else []):
    notas.append("'requests' nas dependências: em rota async, use httpx (bloqueio trava o event loop)")

if problemas:
    print("stack divergente — NÃO escreva rotas com esta skill:", file=sys.stderr)
    for p in problemas:
        print(f"  - {p}", file=sys.stderr)
    print("  → volte a definir-stack; trocar de framework ou migrar Pydantic é decisão (adr-writer).",
          file=sys.stderr)
    raise SystemExit(1)

print(f"ok: {achar('fastapi').strip()}" + (f" · {pyd.strip()}" if pyd else ""))
for n in notas:
    print(f"  nota: {n}")
PY
