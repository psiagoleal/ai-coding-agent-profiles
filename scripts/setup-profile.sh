#!/usr/bin/env bash
# Caminho relativo: scripts/setup-profile.sh
#
# Copia um perfil de regramento de agentes de IA para um repositório alvo e
# gerencia a instalação das skills de governança.
#
# Modelo de skills (independente de agente):
#   - A biblioteca de skills é copiada para uma pasta NEUTRA no alvo (padrão: skills/),
#     que é a fonte única da verdade, versionável e revisável.
#   - Opcionalmente, geramos ADAPTADORES por agente (ex.: .claude/skills/ para o Claude
#     Code), por padrão como SYMLINKS para a pasta neutra — sem duplicar conteúdo.
#
# Uso:
#   scripts/setup-profile.sh <perfil> <repo-alvo> [opções]
#
#   <perfil>     empresa | externo-confidencial | pessoal
#   <repo-alvo>  caminho do repositório de destino
#
# Opções:
#   --skills-mode <modo>   symlink (padrão) | copy | none   (como gerar o adaptador do agente)
#   --agent <agente>       claude (padrão) | none           (qual adaptador gerar)
#   --skills <lista>       lista separada por vírgula (padrão: todas da biblioteca)
#   --neutral-dir <nome>   nome da pasta neutra de skills no alvo (padrão: skills)
#   --config <arquivo>     config TOML com dados pessoais (padrão: config.toml na raiz;
#                          fallback: config.example.toml). Substitui placeholders {{...}}.
#   --force                sobrescreve arquivos já existentes no alvo
#   --dry-run              apenas mostra o que faria, sem escrever
#   -h, --help             esta ajuda
#
# Dados pessoais: copie config.example.toml para config.toml e ajuste. O script substitui
# {{AUTHOR_NAME}}, {{COPYRIGHT_YEAR}}, {{SUPPORT_LABEL}} e {{SUPPORT_URL}} nos arquivos copiados.
#
# Exemplos:
#   scripts/setup-profile.sh empresa ~/dev/meu-projeto
#   scripts/setup-profile.sh pessoal ~/dev/oss --skills-mode copy
#   scripts/setup-profile.sh externo-confidencial ./cliente-x --skills secrets-guard,pr-review-guard
#   scripts/setup-profile.sh empresa ./alvo --dry-run

set -euo pipefail

# ----------------------------------------------------------------------------
# Localização do framework (raiz = pasta-pai de scripts/)
# ----------------------------------------------------------------------------
FRAMEWORK_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROFILES_DIR="$FRAMEWORK_DIR/profiles"
SKILLS_DIR="$FRAMEWORK_DIR/skills"

# ----------------------------------------------------------------------------
# Padrões
# ----------------------------------------------------------------------------
SKILLS_MODE="symlink"
AGENT="claude"
NEUTRAL_DIR="skills"
SKILLS_SELECTED=""
FORCE=0
DRY_RUN=0
CONFIG_FILE=""

PROFILE=""
TARGET=""

# Dados pessoais carregados do config TOML (preenchidos após o parsing).
HAVE_CONFIG=0
CFG_AUTHOR_NAME=""
CFG_COPYRIGHT_YEAR=""
CFG_SUPPORT_LABEL=""
CFG_SUPPORT_URL=""

# ----------------------------------------------------------------------------
# Funções auxiliares
# ----------------------------------------------------------------------------
# Imprime o bloco de comentário de cabeçalho (linhas de # contíguas após o shebang).
usage() { awk 'NR>1 && /^#/ {sub(/^# ?/,""); print; next} NR>1 {exit}' "${BASH_SOURCE[0]}"; }

erro() { printf '\033[31mErro:\033[0m %s\n' "$*" >&2; exit 1; }
info() { printf '\033[36m›\033[0m %s\n' "$*"; }

# Lê uma chave de string `chave = "valor"` do TOML (ignora a seção; primeira ocorrência).
toml_get() {
  sed -n -E "s/^[[:space:]]*$1[[:space:]]*=[[:space:]]*\"([^\"]*)\".*/\1/p" "$CONFIG_FILE" | head -n1
}

# Escapa um valor para uso seguro no lado direito de s|...|...| do sed.
sed_escape_repl() { printf '%s' "$1" | sed -e 's/[&|\\]/\\&/g'; }

# Substitui os placeholders {{...}} de um arquivo copiado pelos valores do config.
apply_substitutions() {
  local file="$1"
  [[ $HAVE_CONFIG -eq 1 && -f "$file" ]] || return 0
  sed -i \
    -e "s|{{AUTHOR_NAME}}|$(sed_escape_repl "$CFG_AUTHOR_NAME")|g" \
    -e "s|{{COPYRIGHT_YEAR}}|$(sed_escape_repl "$CFG_COPYRIGHT_YEAR")|g" \
    -e "s|{{SUPPORT_LABEL}}|$(sed_escape_repl "$CFG_SUPPORT_LABEL")|g" \
    -e "s|{{SUPPORT_URL}}|$(sed_escape_repl "$CFG_SUPPORT_URL")|g" \
    "$file"
}

# Copia um arquivo respeitando --force / --dry-run; pula se já existir.
copy_one() {
  local src="$1" dst="$2"
  if [[ -e "$dst" && $FORCE -eq 0 ]]; then
    printf '  pulado (já existe): %s\n' "$dst"; return 0
  fi
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '  [dry-run] copiaria: %s\n' "$dst"; return 0
  fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  apply_substitutions "$dst"
  printf '  criado: %s\n' "$dst"
}

# ----------------------------------------------------------------------------
# Parsing de argumentos
# ----------------------------------------------------------------------------
while [[ $# -gt 0 ]]; do
  case "$1" in
    -h|--help) usage; exit 0 ;;
    --skills-mode) SKILLS_MODE="${2:-}"; shift 2 ;;
    --agent)       AGENT="${2:-}"; shift 2 ;;
    --skills)      SKILLS_SELECTED="${2:-}"; shift 2 ;;
    --neutral-dir) NEUTRAL_DIR="${2:-}"; shift 2 ;;
    --config)      CONFIG_FILE="${2:-}"; shift 2 ;;
    --force)       FORCE=1; shift ;;
    --dry-run)     DRY_RUN=1; shift ;;
    -*)            erro "opção desconhecida: $1 (use --help)" ;;
    *)
      if [[ -z "$PROFILE" ]]; then PROFILE="$1"
      elif [[ -z "$TARGET" ]]; then TARGET="$1"
      else erro "argumento posicional extra: $1"
      fi
      shift ;;
  esac
done

# ----------------------------------------------------------------------------
# Validação
# ----------------------------------------------------------------------------
[[ -n "$PROFILE" && -n "$TARGET" ]] || { usage; exit 1; }

PROFILE_SRC="$PROFILES_DIR/$PROFILE"
[[ -d "$PROFILE_SRC" ]] || erro "perfil inválido: '$PROFILE'. Opções: empresa | externo-confidencial | pessoal"

case "$SKILLS_MODE" in symlink|copy|none) ;; *) erro "--skills-mode inválido: '$SKILLS_MODE' (symlink|copy|none)";; esac
case "$AGENT"       in claude|none) ;;       *) erro "--agent inválido: '$AGENT' (claude|none)";; esac

# Resolve o arquivo de config: --config > config.toml > config.example.toml.
if [[ -z "$CONFIG_FILE" ]]; then
  if [[ -f "$FRAMEWORK_DIR/config.toml" ]]; then CONFIG_FILE="$FRAMEWORK_DIR/config.toml"
  elif [[ -f "$FRAMEWORK_DIR/config.example.toml" ]]; then CONFIG_FILE="$FRAMEWORK_DIR/config.example.toml"
  fi
fi
if [[ -n "$CONFIG_FILE" && -f "$CONFIG_FILE" ]]; then
  HAVE_CONFIG=1
  CFG_AUTHOR_NAME="$(toml_get author_name)"
  CFG_COPYRIGHT_YEAR="$(toml_get copyright_year)"
  CFG_SUPPORT_LABEL="$(toml_get support_label)"
  CFG_SUPPORT_URL="$(toml_get support_url)"
elif [[ -n "$CONFIG_FILE" ]]; then
  erro "config não encontrado: '$CONFIG_FILE'"
fi

if [[ ! -d "$TARGET" ]]; then
  if [[ $DRY_RUN -eq 1 ]]; then info "[dry-run] criaria diretório alvo: $TARGET"
  else mkdir -p "$TARGET"; info "diretório alvo criado: $TARGET"; fi
fi
TARGET="$(cd "$TARGET" 2>/dev/null && pwd || echo "$TARGET")"

info "Perfil:      $PROFILE"
info "Alvo:        $TARGET"
info "Skills:      neutra='$NEUTRAL_DIR'  adaptador='$AGENT'  modo='$SKILLS_MODE'"
if [[ $HAVE_CONFIG -eq 1 ]]; then
  info "Config:      $CONFIG_FILE (autor='$CFG_AUTHOR_NAME')"
  [[ "$(basename "$CONFIG_FILE")" == "config.example.toml" ]] && \
    info "             (usando o exemplo — copie para config.toml e ajuste seus dados)"
else
  info "Config:      nenhuma — placeholders {{...}} permanecerão nos arquivos."
fi
[[ $DRY_RUN -eq 1 ]] && info "(modo dry-run — nada será escrito)"
echo

# ----------------------------------------------------------------------------
# 1) Copiar os arquivos de instrução do perfil
#    (exclui .claude/skills/* — os adaptadores são gerados na etapa 3)
# ----------------------------------------------------------------------------
info "1) Arquivos de instrução do perfil"
while IFS= read -r -d '' f; do
  rel="${f#"$PROFILE_SRC"/}"
  copy_one "$f" "$TARGET/$rel"
done < <(find "$PROFILE_SRC" -type f -not -path "*/.claude/skills/*" -print0)
echo

# ----------------------------------------------------------------------------
# 2) Copiar a biblioteca de skills para a pasta NEUTRA (fonte da verdade)
# ----------------------------------------------------------------------------
info "2) Biblioteca de skills (pasta neutra: $NEUTRAL_DIR/)"

# Descobre as skills disponíveis (diretórios com SKILL.md)
mapfile -t ALL_SKILLS < <(find "$SKILLS_DIR" -mindepth 2 -maxdepth 2 -name SKILL.md -printf '%h\n' | xargs -n1 basename | sort)

# Resolve a seleção
if [[ -n "$SKILLS_SELECTED" ]]; then
  IFS=',' read -r -a SKILLS <<< "$SKILLS_SELECTED"
else
  SKILLS=("${ALL_SKILLS[@]}")
fi

# Copia o README da biblioteca e cada skill selecionada
copy_one "$SKILLS_DIR/README.md" "$TARGET/$NEUTRAL_DIR/README.md"
for s in "${SKILLS[@]}"; do
  s="${s// /}"; [[ -z "$s" ]] && continue
  [[ -d "$SKILLS_DIR/$s" ]] || erro "skill inexistente: '$s'. Disponíveis: ${ALL_SKILLS[*]}"
  while IFS= read -r -d '' f; do
    rel="${f#"$SKILLS_DIR"/}"
    copy_one "$f" "$TARGET/$NEUTRAL_DIR/$rel"
  done < <(find "$SKILLS_DIR/$s" -type f -print0)
done
echo

# ----------------------------------------------------------------------------
# 3) Gerar adaptadores do agente (ponteiros para a pasta neutra)
# ----------------------------------------------------------------------------
if [[ "$AGENT" == "claude" && "$SKILLS_MODE" != "none" ]]; then
  ADAPTER_DIR="$TARGET/.claude/skills"
  info "3) Adaptador Claude Code em .claude/skills/ (modo: $SKILLS_MODE)"
  for s in "${SKILLS[@]}"; do
    s="${s// /}"; [[ -z "$s" ]] && continue
    local_dst="$ADAPTER_DIR/$s"
    if [[ -e "$local_dst" && $FORCE -eq 0 ]]; then
      printf '  pulado (já existe): %s\n' "$local_dst"; continue
    fi
    if [[ $DRY_RUN -eq 1 ]]; then
      printf '  [dry-run] %s -> %s\n' "$local_dst" "$SKILLS_MODE"; continue
    fi
    mkdir -p "$ADAPTER_DIR"
    rm -rf "$local_dst"
    if [[ "$SKILLS_MODE" == "symlink" ]]; then
      # caminho relativo a partir de .claude/skills/ até a pasta neutra (dois níveis acima)
      ln -s "../../$NEUTRAL_DIR/$s" "$local_dst"
      printf '  symlink: %s -> ../../%s/%s\n' "$local_dst" "$NEUTRAL_DIR" "$s"
    else
      cp -r "$SKILLS_DIR/$s" "$local_dst"
      printf '  cópia:   %s\n' "$local_dst"
    fi
  done
  echo
else
  info "3) Adaptador de agente desabilitado (skills disponíveis apenas na pasta neutra '$NEUTRAL_DIR/')."
  echo
fi

# ----------------------------------------------------------------------------
# Conclusão e próximos passos
# ----------------------------------------------------------------------------
info "Concluído."
cat <<EOF

Próximos passos no repositório alvo:
  1. Ajuste 'AGENTS.md' (seções "Comandos exatos" e "Estrutura de diretórios") ao projeto.
  2. Confira '.gitignore' e '.claudeignore' cobrindo '.env' e dados sensíveis.
  3. Renomeie/preencha '.env' a partir de '.env.example' (NUNCA versione o '.env' real).
  4. Carregue segredos do cofre em tempo de execução (ver skill 'secrets-guard').
EOF
if [[ "$SKILLS_MODE" == "symlink" ]]; then
  cat <<EOF
  Nota: o adaptador usa symlinks. Em checkouts no Windows, considere
        '--skills-mode copy' para máxima portabilidade.
EOF
fi

exit 0
