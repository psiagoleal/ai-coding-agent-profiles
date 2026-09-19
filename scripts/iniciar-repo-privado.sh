#!/usr/bin/env bash
# Caminho relativo: scripts/iniciar-repo-privado.sh
#
# Inicia git num diretório que ainda não é repositório, cria o remoto PRIVADO no GitHub e
# envia o primeiro commit — com as checagens que evitam publicar o que não devia.
#
# Uso:
#   scripts/iniciar-repo-privado.sh <dir> [<dir>...]        # SIMULA (padrão)
#   scripts/iniciar-repo-privado.sh --raiz ~/dev            # simula em todo subdiretório sem git
#   scripts/iniciar-repo-privado.sh --raiz ~/dev --aplicar  # executa
#
# Opções:
#   --aplicar          executa de verdade (sem isto, nada é criado nem enviado)
#   --raiz <dir>       processa cada subdiretório de <dir> (um nível) que não seja repositório
#   --owner <nome>     dono do repositório no GitHub (padrão: a conta autenticada no gh)
#   --prefixo <texto>  prefixo no nome do remoto (ex.: --prefixo trabalho- → trabalho-siph)
#   --sem-push         cria o remoto e commita, mas não envia (você revisa antes)
#
# O que ele RECUSA fazer (por diretório, seguindo para o próximo):
#   - diretório que já é repositório git, ou que está dentro de um;
#   - segredo rastreável (.env, chave privada, credentials.json…) fora do .gitignore;
#   - arquivo > 50 MB fora do .gitignore (o GitHub rejeita acima de 100 MB);
#   - nome de repositório já existente na conta.
#
# O que ele SEMPRE faz antes de commitar: garante um bloco de .gitignore com segredos,
# caches e os backups do framework; confere o que ficou de fato no índice; e, depois de
# criar, confirma que o repositório é PRIVATE.
set -uo pipefail

APLICAR=0; RAIZ=""; OWNER=""; PREFIXO=""; PUSH=1; DIRS=()
erro() { printf '\033[31mErro:\033[0m %s\n' "$*" >&2; exit 1; }
aviso() { printf '  \033[33m!\033[0m %s\n' "$*"; }
ok()   { printf '  \033[32m✓\033[0m %s\n' "$*"; }

while [[ $# -gt 0 ]]; do
  case "$1" in
    --aplicar) APLICAR=1; shift ;;
    --raiz)    RAIZ="${2:-}"; shift 2 ;;
    --owner)   OWNER="${2:-}"; shift 2 ;;
    --prefixo) PREFIXO="${2:-}"; shift 2 ;;
    --sem-push) PUSH=0; shift ;;
    -h|--help) sed -n '2,30p' "$0" | sed 's/^# \{0,1\}//'; exit 0 ;;
    -*) erro "opção desconhecida: $1" ;;
    *)  DIRS+=("$1"); shift ;;
  esac
done

command -v git >/dev/null || erro "git ausente"
command -v gh  >/dev/null || erro "gh ausente (https://cli.github.com)"
gh auth status >/dev/null 2>&1 || erro "gh não autenticado — rode 'gh auth login'"
[[ -n "$OWNER" ]] || OWNER="$(gh api user -q .login)"

if [[ -n "$RAIZ" ]]; then
  [[ -d "$RAIZ" ]] || erro "raiz inexistente: $RAIZ"
  while IFS= read -r d; do [[ -d "$d/.git" ]] || DIRS+=("$d"); done \
    < <(find "$RAIZ" -mindepth 1 -maxdepth 1 -type d | sort)
fi
[[ ${#DIRS[@]} -gt 0 ]] || erro "nada a fazer: passe diretórios ou --raiz <dir>"

# Padrões de segredo: casam pelo nome do arquivo, em qualquer profundidade.
SEGREDOS=(".env" ".env.*" "*.pem" "*.key" "*.p12" "*.pfx" "id_rsa*" "id_ed25519*"
          "credentials.json" "service-account*.json" ".npmrc" ".pypirc" "*.kdbx")
IGNORE_BLOCO='# --- iniciar-repo-privado.sh: nunca versionar ---
.env
.env.*
!.env.example
*.pem
*.key
*.p12
*.pfx
id_rsa*
id_ed25519*
credentials.json
service-account*.json
.npmrc
.pypirc
*.kdbx
# caches e ambientes
__pycache__/
*.pyc
node_modules/
.venv/
venv/
.cache/
target/
dist/
build/
# estado local do agente e backups do framework
.agentry/index/
.agentry/session/
.backup-framework-*.tar.gz
# --- fim do bloco ---'

processar() {
  local dir="$1"
  dir="$(cd "$dir" 2>/dev/null && pwd)" || { aviso "inacessível: $1"; return 1; }
  local nome; nome="$PREFIXO$(basename "$dir" | tr '[:upper:]' '[:lower:]' | tr -c 'a-z0-9._-' '-' | sed 's/-\+/-/g; s/^-//; s/-$//')"
  printf '\n\033[36m›\033[0m %s  →  %s/%s\n' "$dir" "$OWNER" "$nome"

  [[ -d "$dir/.git" ]] && { aviso "já é repositório git — pulado"; return 1; }
  local topo; topo="$(git -C "$dir" rev-parse --show-toplevel 2>/dev/null)"
  [[ -n "$topo" ]] && { aviso "está DENTRO do repositório $topo — pulado (evita repo aninhado)"; return 1; }
  gh repo view "$OWNER/$nome" >/dev/null 2>&1 && { aviso "já existe $OWNER/$nome no GitHub — pulado"; return 1; }

  # .gitignore: garante o bloco antes de qualquer 'git add'
  local gi="$dir/.gitignore" tinha=1
  if [[ ! -f "$gi" ]] || ! grep -q 'iniciar-repo-privado.sh: nunca versionar' "$gi"; then
    tinha=0
    if [[ $APLICAR -eq 1 ]]; then
      [[ -f "$gi" ]] && printf '\n' >> "$gi"
      printf '%s\n' "$IGNORE_BLOCO" >> "$gi"
    fi
  fi
  if [[ $tinha -eq 0 ]]; then
    if [[ $APLICAR -eq 1 ]]; then ok ".gitignore $([[ -s $gi ]] && echo complementado || echo criado)"
    else ok "[simulação] .gitignore seria $([[ -f $gi ]] && echo complementado || echo criado)"; fi
  fi

  # Segredos e arquivos grandes que NÃO seriam ignorados.
  # A varredura poda os diretórios cobertos pelo bloco de .gitignore acima — `git check-ignore`
  # não serve aqui: fora de um repositório ele falha, e em simulação o .gitignore ainda nem
  # foi escrito, o que faria tudo dentro de .venv/ contar como versionável.
  local PODA=(.git .venv venv node_modules __pycache__ target dist build .cache)
  local poda=(); for d in "${PODA[@]}"; do poda+=(-name "$d" -o); done; unset 'poda[${#poda[@]}-1]'
  local achados=() grandes=()
  local args=(); for p in "${SEGREDOS[@]}"; do args+=(-name "$p" -o); done; unset 'args[${#args[@]}-1]'
  while IFS= read -r f; do
    [[ "$(basename "$f")" == ".env.example" ]] && continue
    achados+=("${f#$dir/}")
  done < <(find "$dir" \( "${poda[@]}" \) -prune -o -type f \( "${args[@]}" \) -print 2>/dev/null)
  while IFS= read -r f; do
    grandes+=("${f#$dir/} ($(du -h "$f" | cut -f1))")
  done < <(find "$dir" \( "${poda[@]}" \) -prune -o -type f -size +50M -print 2>/dev/null)

  if [[ ${#achados[@]} -gt 0 ]]; then
    aviso "SEGREDO fora do .gitignore (${#achados[@]}) — nada será criado:"
    printf '      %s\n' "${achados[@]:0:10}"
    printf '      Mova para fora do repositório, ou acrescente ao .gitignore, e rode de novo.\n'
    return 1
  fi
  if [[ ${#grandes[@]} -gt 0 ]]; then
    aviso "arquivo grande fora do .gitignore (${#grandes[@]}) — nada será criado:"
    printf '      %s\n' "${grandes[@]:0:10}"
    return 1
  fi
  ok "sem segredo nem arquivo grande a versionar"

  if [[ $APLICAR -eq 0 ]]; then
    printf '  \033[90m[simulação] criaria %s/%s (privado), commit inicial e %s\033[0m\n' \
      "$OWNER" "$nome" "$([[ $PUSH -eq 1 ]] && echo 'push' || echo 'sem push')"
    return 0
  fi

  git -C "$dir" init -q -b main || { aviso "falha no git init"; return 1; }
  git -C "$dir" add -A || { aviso "falha no git add"; return 1; }
  # Conferência final: o índice não pode conter segredo
  local no_indice; no_indice="$(git -C "$dir" ls-files | grep -E '(^|/)(\.env$|\.env\.[^/]*$|credentials\.json$|.*\.(pem|key|p12|pfx|kdbx)$|id_rsa|id_ed25519)' | grep -v '\.env\.example$' || true)"
  if [[ -n "$no_indice" ]]; then
    aviso "segredo chegou ao índice — abortado, nada foi enviado:"; printf '      %s\n' $no_indice
    rm -rf "$dir/.git"; return 1
  fi
  git -C "$dir" -c user.useConfigOnly=false commit -q -m "chore: commit inicial

Repositorio iniciado por scripts/iniciar-repo-privado.sh, com .gitignore de
segredos, caches e backups do framework aplicado antes do primeiro add." || { aviso "falha no commit"; return 1; }
  ok "commit inicial: $(git -C "$dir" rev-list --count HEAD) commit, $(git -C "$dir" ls-files | wc -l) arquivos"

  local flags=(--private --source "$dir" --remote origin)
  [[ $PUSH -eq 1 ]] && flags+=(--push)
  gh repo create "$OWNER/$nome" "${flags[@]}" >/dev/null 2>&1 || { aviso "falha ao criar $OWNER/$nome"; return 1; }
  local vis; vis="$(gh repo view "$OWNER/$nome" --json visibility -q .visibility 2>/dev/null)"
  [[ "$vis" == "PRIVATE" ]] || { aviso "ATENÇÃO: visibilidade veio '$vis' — verifique imediatamente"; return 1; }
  ok "remoto criado e confirmado PRIVATE$([[ $PUSH -eq 1 ]] && echo ', enviado' || echo ' (sem push)')"
  return 0
}

feitos=0; pulados=0
for d in "${DIRS[@]}"; do processar "$d" && feitos=$((feitos+1)) || pulados=$((pulados+1)); done
printf '\n%s: %d diretório(s) ok, %d pulado(s)\n' \
  "$([[ $APLICAR -eq 1 ]] && echo 'Concluído' || echo 'Simulação')" "$feitos" "$pulados"
[[ $APLICAR -eq 0 ]] && printf 'Nada foi criado. Repita com --aplicar para executar.\n'
exit 0
