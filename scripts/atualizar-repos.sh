#!/usr/bin/env bash
# Caminho relativo: scripts/atualizar-repos.sh
#
# Atualiza a instalação do framework em todos os repositórios de um diretório.
#
#   atualizar-repos.sh [raiz] [--dry-run] [--config ARQ] [--config-publico ARQ]
#                      [--sem-hook] [--incluir a,b] [--excluir c,d]
#
# Para cada subdiretório que já tem o framework instalado:
#   1. descobre o perfil pelo cabeçalho do AGENTS.md;
#   2. pula o que tiver árvore git suja (o --update é revisado por git diff);
#   3. roda setup-profile.sh --update com o config certo;
#   4. instala o hook commit-msg, se ainda não houver.
#
# Perfil PESSOAL é público por definição: recebe apenas a biblioteca pública, com um
# config sem `fontes_extras`. Os demais recebem o config padrão.
#
# Sem --dry-run ele ESCREVE. Revise cada repositório com `git diff` depois.
set -euo pipefail

FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RAIZ="$HOME/dev"
DRY=0
SEM_HOOK=0
CONFIG=""
CONFIG_PUBLICO=""
INCLUIR=""
EXCLUIR=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --dry-run)         DRY=1; shift ;;
    --config)          CONFIG="${2:?}"; shift 2 ;;
    --config-publico)  CONFIG_PUBLICO="${2:?}"; shift 2 ;;
    --sem-hook)        SEM_HOOK=1; shift ;;
    --incluir)         INCLUIR="${2:?}"; shift 2 ;;
    --excluir)         EXCLUIR="${2:?}"; shift 2 ;;
    -h|--help)         sed -n '3,20p' "$0" | sed 's/^# \?//'; exit 0 ;;
    -*)                printf 'opção desconhecida: %s\n' "$1" >&2; exit 2 ;;
    *)                 RAIZ="$1"; shift ;;
  esac
done

[[ -d "$RAIZ" ]] || { printf 'raiz inexistente: %s\n' "$RAIZ" >&2; exit 2; }

# Um config público padrão (sem fontes_extras) é gerado se nenhum for passado: garante
# que repositório público nunca receba a biblioteca privada, mesmo que o config pessoal
# do usuário a inclua.
if [[ -z "$CONFIG_PUBLICO" ]]; then
  CONFIG_PUBLICO="$(mktemp)"; trap 'rm -f "$CONFIG_PUBLICO"' EXIT
  if [[ -f "$FRAMEWORK_DIR/config.toml" ]]; then
    grep -v -E '^\s*(fontes_extras|fonte)\s*=' "$FRAMEWORK_DIR/config.toml" > "$CONFIG_PUBLICO"
  else
    : > "$CONFIG_PUBLICO"
  fi
fi

em_lista() { local alvo="$1" lista="$2"; [[ ",$lista," == *",$alvo,"* ]]; }

perfil_de() {  # lê o cabeçalho do AGENTS.md instalado
  local agents="$1"
  case "$(head -5 "$agents" | tr '[:upper:]' '[:lower:]')" in
    *"perfil pessoal"*)               echo pessoal ;;
    *"perfil externo-confidencial"*)  echo externo-confidencial ;;
    *"perfil empresa"*)               echo empresa ;;
    *)                                echo "" ;;
  esac
}

atualizados=(); pulados=(); falhos=()

for dir in "$RAIZ"/*/; do
  repo="$(basename "${dir%/}")"
  [[ -n "$INCLUIR" ]] && ! em_lista "$repo" "$INCLUIR" && continue
  [[ -n "$EXCLUIR" ]] && em_lista "$repo" "$EXCLUIR" && continue
  [[ "$(cd "${dir%/}" && pwd)" == "$FRAMEWORK_DIR" ]] && continue   # não se atualiza sozinho
  [[ -f "${dir}AGENTS.md" ]] || continue
  [[ -d "${dir}skills" || -d "${dir}.agent-profile" ]] || continue

  perfil="$(perfil_de "${dir}AGENTS.md")"
  if [[ -z "$perfil" ]]; then
    pulados+=("$repo (perfil não reconhecido no AGENTS.md)"); continue
  fi
  if [[ ! -d "${dir}.git" ]]; then
    pulados+=("$repo (sem git: --update não seria revisável)"); continue
  fi
  if [[ -n "$(git -C "${dir%/}" status --porcelain)" ]]; then
    pulados+=("$repo (árvore suja — comite ou guarde antes)"); continue
  fi

  cfg="$CONFIG"
  [[ "$perfil" == pessoal ]] && cfg="$CONFIG_PUBLICO"
  args=("$perfil" "${dir%/}" --update)
  [[ -n "$cfg" ]] && args+=(--config "$cfg")
  (( DRY )) && args+=(--dry-run)

  printf '\033[36m›\033[0m %-28s perfil=%-20s %s\n' "$repo" "$perfil" "$( ((DRY)) && echo '[dry-run]')"
  if bash "$FRAMEWORK_DIR/scripts/setup-profile.sh" "${args[@]}" > "${TMPDIR:-/tmp}/atualizar-$repo.log" 2>&1; then
    atualizados+=("$repo")
  else
    falhos+=("$repo (ver ${TMPDIR:-/tmp}/atualizar-$repo.log)")
    continue
  fi

  # Hook commit-msg: barra link de sessão e afins na mensagem (skill pr-review-guard).
  hook="${dir}.git/hooks/commit-msg"
  origem="${dir}skills/pr-review-guard/scripts/checar-mensagem-commit.sh"
  if (( ! SEM_HOOK )) && [[ -f "$origem" && ! -e "$hook" ]]; then
    if (( DRY )); then
      printf '    [dry-run] instalaria hook commit-msg\n'
    else
      ln -sf ../../skills/pr-review-guard/scripts/checar-mensagem-commit.sh "$hook"
      printf '    hook commit-msg instalado\n'
    fi
  fi
done

printf '\n\033[1mResumo\033[0m — %d atualizado(s), %d pulado(s), %d falha(s)\n' \
  "${#atualizados[@]}" "${#pulados[@]}" "${#falhos[@]}"
((${#pulados[@]})) && printf '  pulado: %s\n' "${pulados[@]}"
((${#falhos[@]}))  && printf '  \033[31mfalha:\033[0m %s\n' "${falhos[@]}"
if ((${#atualizados[@]})) && (( ! DRY )); then
  printf '\nRevise antes de commitar:\n'
  for r in "${atualizados[@]}"; do printf '  git -C %s/%s diff\n' "$RAIZ" "$r"; done
fi
exit 0
