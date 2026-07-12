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
#   --update               atualiza um alvo já instalado de forma NÃO-DESTRUTIVA
#                          (atualiza regras, faz merge dos híbridos, preserva os vivos)
#   --force                sobrescreve arquivos já existentes no alvo (instalação)
#   --dry-run              apenas mostra o que faria, sem escrever
#   -h, --help             esta ajuda
#
# Dados pessoais: copie config.example.toml para config.toml e ajuste. O script substitui
# {{AUTHOR_NAME}}, {{COPYRIGHT_YEAR}}, {{SUPPORT_LABEL}} e {{SUPPORT_URL}} nos arquivos copiados.
#
# Modo --update (atualização não-destrutiva de uma instalação existente):
#   Os arquivos do alvo são classificados em três baldes:
#     - REGRA/ponteiro (CLAUDE.md, .cursorrules, copilot-instructions, skills): sobrescritos.
#     - HÍBRIDO de texto (AGENTS.md, .claudeignore, .env.example): merge por seção — o miolo
#       entre marcadores `USER:BEGIN id=... / USER:END` é PRESERVADO; o resto é regenerado.
#     - HÍBRIDO JSON (.claude/settings.json, .agentry/agentry.settings.json — ADR-0006/
#       agentry-ADR-0018): deep-merge via `jq` (requer jq); regra vence em conflito, chaves
#       extras do usuário são preservadas.
#     - VIVO (docs/CURRENT-STATE.md, docs/adr/NNNN-*.md, .env): nunca tocados.
#   Arquivos novos (ausentes no alvo) são sempre criados. Nada é apagado. Use com --dry-run
#   para revisar o plano antes. Recomenda-se árvore git limpa no alvo (revise com `git diff`).
#
# Exemplos:
#   scripts/setup-profile.sh empresa ~/dev/meu-projeto
#   scripts/setup-profile.sh pessoal ~/dev/oss --skills-mode copy
#   scripts/setup-profile.sh externo-confidencial ./cliente-x --skills secrets-guard,pr-review-guard
#   scripts/setup-profile.sh empresa ./alvo --dry-run
#   scripts/setup-profile.sh empresa ./alvo --update --dry-run     # plano de atualização
#   scripts/setup-profile.sh empresa ./alvo --update               # atualiza sem destruir

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
UPDATE=0
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
# Atualização não-destrutiva (--update)
# ----------------------------------------------------------------------------
# Classifica um caminho relativo do perfil em: rule | hybrid_text | hybrid_json | live.
bucket_for() {
  case "$1" in
    docs/CURRENT-STATE.md|docs/adr/[0-9]*|.env)             echo live ;;
    AGENTS.md|.claudeignore|.env.example)                   echo hybrid_text ;;
    .claude/settings.json|.agentry/agentry.settings.json)   echo hybrid_json ;;
    *)                                                       echo rule ;;
  esac
}

# Estilo de comentário do marcador conforme o tipo de arquivo (para blocos órfãos).
comment_style_for() { case "$1" in *.md) echo html ;; *) echo hash ;; esac; }

# Sobrescreve um arquivo de REGRA (reaplica substituições), respeitando --dry-run.
overwrite_file() {
  local src="$1" dst="$2"
  if [[ $DRY_RUN -eq 1 ]]; then printf '  [dry-run] atualizaria (regra):    %s\n' "$dst"; return 0; fi
  mkdir -p "$(dirname "$dst")"
  cp "$src" "$dst"
  apply_substitutions "$dst"
  printf '  atualizado (regra):    %s\n' "$dst"
}

# Merge de híbrido de TEXTO: preserva as ilhas USER:* do alvo, regenera o resto do template.
# Args: src(template) dst(alvo) rel(caminho relativo, para estilo de comentário).
update_text_hybrid() {
  local src="$1" dst="$2" rel="$3"

  # Híbrido legado, sem marcadores no alvo: não regenera (evita perda) — emite .new.
  if ! grep -q 'USER:BEGIN id=' "$dst"; then
    if [[ $DRY_RUN -eq 1 ]]; then
      printf '  [dry-run] legado sem marcadores: geraria %s.new\n' "$dst"; return 0
    fi
    cp "$src" "$dst.new"; apply_substitutions "$dst.new"
    printf '  \033[33mlegado sem marcadores\033[0m: gravado %s.new (faça o merge manual)\n' "$dst"
    return 0
  fi

  local idir; idir="$(mktemp -d)"
  : > "$idir/.ids"

  # 1) Extrai as ilhas USER:* do alvo; valida o balanceamento dos marcadores.
  # (USER:ORPHAN também abre bloco — para que a reextração seja idempotente.)
  if ! awk -v dir="$idir" '
    /USER:(BEGIN|ORPHAN) id=/ {
      if (inblk) exit 2
      id=$0; sub(/.*id=/,"",id); sub(/[^A-Za-z0-9._-].*/,"",id)
      inblk=1; cur=dir"/island." id; print id >> dir"/.ids"; next
    }
    /USER:END/ { if (!inblk) exit 2; inblk=0; next }
    { if (inblk) print >> cur }
    END { if (inblk) exit 2 }
  ' "$dst"; then
    rm -rf "$idir"; erro "marcadores USER desbalanceados em $dst (corrija os pares BEGIN/END)"
  fi

  # 2) Renderiza o template (aplica substituições {{...}} numa cópia temporária).
  local rendered; rendered="$(mktemp)"
  cp "$src" "$rendered"; apply_substitutions "$rendered"

  # 3) Reassembla: para cada ilha do template, reinjeta o conteúdo salvo do alvo (por id).
  local out; out="$(mktemp)"
  awk -v dir="$idir" '
    BEGIN { idf=dir"/.ids"; while ((getline x < idf) > 0) has[x]=1; close(idf) }
    /USER:BEGIN id=/ {
      print
      id=$0; sub(/.*id=/,"",id); sub(/[^A-Za-z0-9._-].*/,"",id)
      if (id in has) { f=dir"/island." id; while ((getline l < f) > 0) print l; close(f); skip=1 }
      else skip=0
      inblk=1; next
    }
    /USER:END/ { print; inblk=0; skip=0; next }
    { if (inblk && skip) next; print }
  ' "$rendered" > "$out"

  # 4) Blocos órfãos: ids do alvo que sumiram do template — preserva ao final + avisa.
  local tmpl_ids tgt_ids orphans style
  tmpl_ids="$(sed -n 's/.*USER:BEGIN id=\([A-Za-z0-9._-]*\).*/\1/p' "$src" | sort -u)"
  tgt_ids="$(sort -u "$idir/.ids")"
  orphans="$(comm -23 <(printf '%s\n' "$tgt_ids") <(printf '%s\n' "$tmpl_ids"))"
  style="$(comment_style_for "$rel")"
  local n_islands n_orphans
  n_islands="$(grep -c . "$idir/.ids" 2>/dev/null || echo 0)"
  n_orphans="$(printf '%s' "$orphans" | grep -c . || true)"

  local oid
  while IFS= read -r oid; do
    [[ -z "$oid" ]] && continue
    if [[ "$style" == html ]]; then
      { printf '\n<!-- USER:ORPHAN id=%s — seção removida do framework; preservada para revisão -->\n' "$oid"
        cat "$idir/island.$oid" 2>/dev/null
        printf '<!-- USER:END -->\n'; } >> "$out"
    else
      { printf '\n# USER:ORPHAN id=%s — seção removida do framework; preservada para revisão\n' "$oid"
        cat "$idir/island.$oid" 2>/dev/null
        printf '# USER:END\n'; } >> "$out"
    fi
  done <<< "$orphans"

  # 5) Grava (ou apenas relata, em dry-run).
  local msg="atualizado (merge):    $dst — ${n_islands} ilha(s) preservada(s)"
  [[ "$n_orphans" -gt 0 ]] && msg+=", ${n_orphans} órfã(s)"
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '  [dry-run] %s\n' "$msg"
  else
    mv "$out" "$dst"
    printf '  %s\n' "$msg"
    [[ "$n_orphans" -gt 0 ]] && printf '  \033[33maviso:\033[0m ilha(s) órfã(s) preservadas ao final de %s: %s\n' "$dst" "$(printf '%s ' $orphans)"
  fi

  rm -f "$rendered"; [[ -f "$out" ]] && rm -f "$out"; rm -rf "$idir"
}

# Merge de híbrido JSON (.claude/settings.json) via jq: regra vence, chaves do usuário ficam.
update_json_settings() {
  local src="$1" dst="$2"
  command -v jq >/dev/null 2>&1 || \
    erro "jq é necessário para atualizar $dst (instale: 'sudo apt install jq'). Sem jq, edite o settings.json manualmente."
  if [[ $DRY_RUN -eq 1 ]]; then printf '  [dry-run] mesclaria (jq):       %s\n' "$dst"; return 0; fi
  local tmp; tmp="$(mktemp)"
  if jq -s '.[0] * .[1]' "$dst" "$src" > "$tmp"; then
    mv "$tmp" "$dst"
    printf '  atualizado (merge jq): %s\n' "$dst"
  else
    rm -f "$tmp"; erro "falha no merge jq de $dst (JSON inválido?)"
  fi
}

# Roteador: instala um arquivo segundo o modo (instalação vs --update) e o balde.
install_file() {
  local rel="$1" src="$2" dst="$3"
  if [[ ! -e "$dst" || $UPDATE -eq 0 ]]; then copy_one "$src" "$dst"; return; fi
  case "$(bucket_for "$rel")" in
    rule)        overwrite_file    "$src" "$dst" ;;
    hybrid_text) update_text_hybrid "$src" "$dst" "$rel" ;;
    hybrid_json) update_json_settings "$src" "$dst" ;;
    live)        printf '  preservado (vivo):     %s\n' "$dst" ;;
  esac
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
    --update)      UPDATE=1; shift ;;
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

info "Modo:        $([[ $UPDATE -eq 1 ]] && echo 'atualização não-destrutiva (--update)' || echo 'instalação')"
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
  install_file "$rel" "$f" "$TARGET/$rel"
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

# Copia (ou atualiza) o README da biblioteca e cada skill selecionada — sempre REGRA.
install_file "README.md" "$SKILLS_DIR/README.md" "$TARGET/$NEUTRAL_DIR/README.md"
for s in "${SKILLS[@]}"; do
  s="${s// /}"; [[ -z "$s" ]] && continue
  [[ -d "$SKILLS_DIR/$s" ]] || erro "skill inexistente: '$s'. Disponíveis: ${ALL_SKILLS[*]}"
  while IFS= read -r -d '' f; do
    rel="${f#"$SKILLS_DIR"/}"
    install_file "$rel" "$f" "$TARGET/$NEUTRAL_DIR/$rel"
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
    if [[ -e "$local_dst" && $FORCE -eq 0 && $UPDATE -eq 0 ]]; then
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
if [[ $UPDATE -eq 1 ]]; then
  cat <<EOF

Atualização concluída. Próximos passos no repositório alvo:
  1. Revise as mudanças com 'git diff' — as ilhas 'USER:*' e os arquivos vivos (ADRs,
     CURRENT-STATE.md, .env) devem estar intactos; só as regras foram atualizadas.
  2. Resolva eventuais arquivos '*.new' (híbridos legados sem marcadores) e blocos
     'USER:ORPHAN' (seções de regra que saíram do framework) por merge manual.
EOF
else
  cat <<EOF

Próximos passos no repositório alvo:
  1. Ajuste 'AGENTS.md' (seções "Comandos exatos" e "Estrutura de diretórios") ao projeto —
     edite DENTRO dos marcadores 'USER:BEGIN/END' para que '--update' preserve suas mudanças.
  2. Confira '.gitignore' e '.claudeignore' cobrindo '.env' e dados sensíveis.
  3. Renomeie/preencha '.env' a partir de '.env.example' (NUNCA versione o '.env' real).
  4. Carregue segredos do cofre em tempo de execução (ver skill 'secrets-guard').
EOF
fi
if [[ "$SKILLS_MODE" == "symlink" ]]; then
  cat <<EOF
  Nota: o adaptador usa symlinks. Em checkouts no Windows, considere
        '--skills-mode copy' para máxima portabilidade.
EOF
fi

exit 0
