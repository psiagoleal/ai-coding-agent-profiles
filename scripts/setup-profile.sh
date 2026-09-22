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
#   --agent <lista>        claude (padrão) | all | none | lista separada por vírgula.
#                          Harnesses: claude, codex, gemini, opencode, agentry, zcode.
#                          Todos exceto 'claude' compartilham '.agents/skills/' — o
#                          caminho de descoberta comum entre harnesses (ADR 0012).
#                          Ex.: --agent claude,codex   |   --agent all
#   --skills <lista>       lista separada por vírgula (padrão: as de governança). Aceita:
#                            nome sem caminho (minha-skill — nomes são únicos no acervo),
#                            caminho (categoria/minha-skill), categoria inteira
#                            ('verificacao/*' — COM aspas, senão o shell expande) e @padrao.
#   --fonte <dir>          biblioteca EXTRA de skills/agents (repetível), ex.: um repositório
#                          privado com a mesma estrutura (skills/, agents/). Também lida de
#                          config.toml: fontes_extras = "dir1:dir2". Nomes devem ser únicos
#                          entre todas as fontes — colisão é erro.
#   --agents <modo>        auto (padrão: os subagents citados pelas skills instaladas) |
#                          all | none | lista separada por vírgula. Vão para a pasta neutra
#                          agents/; o adaptador hoje só existe para claude (.claude/agents).
#                          Skills de domínio moram em categorias e exigem o caminho:
#                          --skills secrets-guard,dominio/mockup-lab
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
#     - ANDAIME (README.md, CHANGELOG.md, LICENSE da raiz): entregues como ponto de
#       partida na instalação, mas a autoria passa ao projeto — nunca sobrescritos.
#   Proteção contra edição local: REGRA e HÍBRIDO de texto têm a impressão digital do
#     esqueleto (arquivo sem o corpo das ilhas) gravada em .agent-profile/baseline.sha256.
#     Se o esqueleto no alvo divergir dela, houve edição FORA das ilhas: o original fica
#     intacto e a versão nova vai para <arquivo>.new. --force sobrescreve. Versione a pasta.
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
AGENTS_SELECTED="auto"
AGENTS_NEUTRAL_DIR="agents"
FORCE=0
DRY_RUN=0
UPDATE=0
CONFIG_FILE=""
FONTES_EXTRAS=()

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
# Classifica um caminho relativo do perfil em: rule | hybrid_text | hybrid_json | live | scaffold.
#
# scaffold: andaime entregue como ponto de partida, mas cuja autoria passa ao projeto
#   assim que existe (README, CHANGELOG, LICENSE). Diferente de `rule` — que é regramento
#   do framework e pode ser regenerado — e de `live`, que é artefato operacional do dia a
#   dia. Sobrescrever um andaime destruiria a documentação real do projeto.
#   Só o nível raiz casa: `docs/adr/README.md` e `<neutra>/README.md` seguem sendo regra.
bucket_for() {
  # O README da biblioteca de skills tem ilha para o catálogo local — híbrido, não regra.
  [[ "$1" == "$NEUTRAL_DIR/README.md" ]] && { echo hybrid_text; return; }
  case "$1" in
    docs/CURRENT-STATE.md|docs/TICKETS.md|docs/architecture.md|docs/DESIGN.md|docs/adr/[0-9]*|.env) echo live ;;
    # docs/adr/README.md é o ÍNDICE dos ADRs do projeto — quem o mantém é o projeto, a cada
    # ADR novo. Regenerá-lo apagaria a lista inteira (o template traz só uma linha-exemplo).
    README.md|CHANGELOG.md|LICENSE|docs/adr/README.md)      echo scaffold ;;
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
  if ! grep -qE '^[[:space:]]*(<!--|#)[[:space:]]*USER:BEGIN id=' "$dst"; then
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
  # Um marcador só conta se a linha COMEÇA com o comentário — assim uma menção em prosa
  # (`USER:BEGIN` citado no meio de uma frase, como na seção 10) não abre nem fecha bloco.
  if ! awk -v dir="$idir" '
    /^[[:space:]]*(<!--|#)[[:space:]]*USER:(BEGIN|ORPHAN) id=/ {
      if (inblk) exit 2
      id=$0; sub(/.*id=/,"",id); sub(/[^A-Za-z0-9._-].*/,"",id)
      inblk=1; cur=dir"/island." id; print id >> dir"/.ids"; next
    }
    /^[[:space:]]*(<!--|#)[[:space:]]*USER:END/ { if (!inblk) exit 2; inblk=0; next }
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
    /^[[:space:]]*(<!--|#)[[:space:]]*USER:BEGIN id=/ {
      print
      id=$0; sub(/.*id=/,"",id); sub(/[^A-Za-z0-9._-].*/,"",id)
      if (id in has) { f=dir"/island." id; while ((getline l < f) > 0) print l; close(f); skip=1 }
      else skip=0
      inblk=1; next
    }
    /^[[:space:]]*(<!--|#)[[:space:]]*USER:END/ { print; inblk=0; skip=0; next }
    { if (inblk && skip) next; print }
  ' "$rendered" > "$out"

  # 4) Blocos órfãos: ids do alvo que sumiram do template — preserva ao final + avisa.
  local tmpl_ids tgt_ids orphans style
  tmpl_ids="$(sed -n -E 's/^[[:space:]]*(<!--|#)[[:space:]]*USER:BEGIN id=([A-Za-z0-9._-]*).*/\2/p' "$src" | sort -u)"
  tgt_ids="$(sort -u "$idir/.ids")"
  orphans="$(comm -23 <(printf '%s\n' "$tgt_ids") <(printf '%s\n' "$tmpl_ids"))"
  style="$(comment_style_for "$rel")"
  local n_islands n_orphans n_rescued
  n_islands="$(grep -c . "$idir/.ids" 2>/dev/null || echo 0)"
  n_orphans="$(printf '%s' "$orphans" | grep -c . || true)"
  n_rescued=0

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

  # 4b) Resgate de linhas editadas FORA das ilhas em arquivos linha-a-linha
  #     (.claudeignore, .env.example). Nesses arquivos cada linha é um controle — um
  #     `secrets/` que some do .claudeignore é uma pasta que volta a ser indexada. A ilha
  #     é o lugar certo, mas a regeneração não pode apagar em silêncio quem não a usou.
  if [[ "$style" == hash ]]; then
    local rescued; rescued="$(mktemp)"
    while IFS= read -r line; do
      [[ -z "${line//[[:space:]]/}" ]] && continue
      [[ "$line" == \#* ]] && continue
      grep -qxF -- "$line" "$out" || printf '%s\n' "$line" >> "$rescued"
    done < "$dst"
    if [[ -s "$rescued" ]]; then
      n_rescued="$(grep -c . "$rescued")"
      { printf '\n# USER:RESCUE — linhas que estavam FORA das ilhas e sumiriam na regeneração.\n'
        printf '# Mova-as para dentro de uma ilha USER para que parem de reaparecer aqui.\n'
        cat "$rescued"; } >> "$out"
    fi
    rm -f "$rescued"
  fi

  # 5) Grava (ou apenas relata, em dry-run).
  local msg="atualizado (merge):    $dst — ${n_islands} ilha(s) preservada(s)"
  [[ "$n_orphans" -gt 0 ]] && msg+=", ${n_orphans} órfã(s)"
  [[ "$n_rescued" -gt 0 ]] && msg+=", ${n_rescued} linha(s) resgatada(s)"
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
  local bucket; bucket="$(bucket_for "$rel")"
  if [[ ! -e "$dst" || $UPDATE -eq 0 ]]; then
    local existia=0; [[ -e "$dst" ]] && existia=1
    copy_one "$src" "$dst"
    # linha de base só do que este script de fato escreveu
    if [[ ( $existia -eq 0 || $FORCE -eq 1 ) && ( "$bucket" == rule || "$bucket" == hybrid_text ) ]]; then
      baseline_set "$rel" "$dst"
    fi
    return
  fi
  case "$bucket" in
    rule|hybrid_text)
      if ! sem_edicao_local "$rel" "$dst"; then desviar_para_new "$bucket" "$src" "$dst" "$rel"; return; fi
      if [[ "$bucket" == rule ]]; then overwrite_file "$src" "$dst"
      else update_text_hybrid "$src" "$dst" "$rel"; fi
      # híbrido legado sem marcadores não foi regenerado (virou .new): não fixa linha de base
      if [[ "$bucket" == rule ]] || grep -qE '^[[:space:]]*(<!--|#)[[:space:]]*USER:BEGIN id=' "$dst"; then
        baseline_set "$rel" "$dst"
      fi
      ;;
    hybrid_json) update_json_settings "$src" "$dst" ;;
    live)        printf '  preservado (vivo):     %s\n' "$dst" ;;
    scaffold)    printf '  preservado (projeto):  %s\n' "$dst" ;;
  esac
}

# ----------------------------------------------------------------------------
# Linha de base: detecta edição local FORA das ilhas antes de regenerar
# ----------------------------------------------------------------------------
# Sem isto, o --update não distingue "o template mudou" de "alguém editou o texto do
# framework no projeto" — e a edição local some em silêncio. A cada escrita, grava-se a
# impressão digital do ESQUELETO do arquivo (o arquivo sem o corpo das ilhas USER:*) em
# <alvo>/.agent-profile/baseline.sha256 (repo-local, versionável — ADR 0011). No --update,
# esqueleto atual diferente da linha de base = edição local: o resultado vai para <arq>.new
# e o original fica intacto. --force sobrescreve assim mesmo.
BASELINE_REL=".agent-profile/baseline.sha256"
CONFLITOS=(); SEM_BASELINE=(); PEND_AGENT_HARNESS=()

frame_hash() {
  awk '
    /^[[:space:]]*(<!--|#)[[:space:]]*USER:(BEGIN|ORPHAN|RESCUE)/ { print; inblk=1; next }
    /^[[:space:]]*(<!--|#)[[:space:]]*USER:END/                 { print; inblk=0; next }
    { if (!inblk) print }' "$1" | sha256sum | cut -c1-64
}
baseline_get() {
  local f="$TARGET/$BASELINE_REL"
  [[ -f "$f" ]] && awk -v r="$1" '{h=$1; $1=""; sub(/^ +/,""); if ($0==r) last=h} END{if (last) print last}' "$f"
}
baseline_set() {  # rel dst
  [[ $DRY_RUN -eq 1 ]] && return 0
  local f="$TARGET/$BASELINE_REL" h; h="$(frame_hash "$2")"
  mkdir -p "$(dirname "$f")"; touch "$f"
  awk -v r="$1" '{l=$0; h=$1; $1=""; sub(/^ +/,""); if ($0!=r) print l}' "$f" > "$f.tmp"
  printf '%s  %s\n' "$h" "$1" >> "$f.tmp"
  sort -k2 "$f.tmp" > "$f" && rm -f "$f.tmp"
}
# 0 = pode regenerar no lugar; 1 = há edição local fora das ilhas (desviar para .new)
sem_edicao_local() {  # rel dst
  [[ $FORCE -eq 1 ]] && return 0
  local base; base="$(baseline_get "$1")"
  if [[ -z "$base" ]]; then SEM_BASELINE+=("$1"); return 0; fi
  [[ "$(frame_hash "$2")" == "$base" ]]
}
# Roda a regeneração numa cópia e entrega o resultado como <dst>.new, sem tocar no original.
desviar_para_new() {  # bucket src dst rel
  local bucket="$1" src="$2" dst="$3" rel="$4" tmpd; tmpd="$(mktemp -d)"
  cp "$dst" "$tmpd/arq"
  if [[ "$bucket" == rule ]]; then
    cp "$src" "$tmpd/arq"; apply_substitutions "$tmpd/arq"
  else
    local salva=$DRY_RUN; DRY_RUN=0
    update_text_hybrid "$src" "$tmpd/arq" "$rel" >/dev/null
    DRY_RUN=$salva
  fi
  CONFLITOS+=("$rel")
  if [[ $DRY_RUN -eq 1 ]]; then
    printf '  [dry-run] \033[33medição local fora das ilhas\033[0m: geraria %s.new\n' "$dst"
  else
    mv "$tmpd/arq" "$dst.new"
    printf '  \033[33medição local fora das ilhas\033[0m: %s preservado; versão nova em %s.new\n' "$dst" "$dst"
  fi
  rm -rf "$tmpd"
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
    --agents)      AGENTS_SELECTED="${2:-}"; shift 2 ;;
    --fonte)       FONTES_EXTRAS+=("${2:-}"); shift 2 ;;
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
# --agent aceita lista; 'all' expande para todos os harnesses conhecidos.
HARNESSES_CONHECIDOS="claude codex gemini opencode agentry zcode"
if [[ "$AGENT" == "all" ]]; then
  AGENT="${HARNESSES_CONHECIDOS// /,}"
fi
if [[ "$AGENT" != "none" ]]; then
  IFS=',' read -r -a _agentes <<< "$AGENT"
  for _a in "${_agentes[@]}"; do
    _a="${_a// /}"; [[ -z "$_a" ]] && continue
    [[ " $HARNESSES_CONHECIDOS " == *" $_a "* ]] || \
      erro "--agent inválido: '$_a' (conhecidos: ${HARNESSES_CONHECIDOS// /, }, all, none)"
  done
fi

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
# 0) Resolver a seleção de skills ANTES de escrever qualquer coisa no alvo
# ----------------------------------------------------------------------------
# (seleção inválida não pode deixar instalação pela metade)
# Descobre as skills disponíveis (diretórios com SKILL.md), em dois níveis:
#   - GOVERNANÇA, na raiz da biblioteca (ex.: 'secrets-guard') — independentes de setor,
#     é o conjunto PADRÃO instalado em qualquer perfil.
#   - DOMÍNIO, agrupadas em categoria (ex.: 'dominio/mockup-lab') — específicas de uma
#     tecnologia ou assunto; nunca entram por padrão, só via --skills explícito.
# Fontes: o framework e, opcionalmente, bibliotecas extras (ex.: repositório privado).
_cfg_fontes="$(toml_get fontes_extras 2>/dev/null || true)"
if [[ -n "$_cfg_fontes" ]]; then IFS=':' read -r -a _cf <<< "$_cfg_fontes"; FONTES_EXTRAS+=("${_cf[@]}"); fi
LIBS=("$FRAMEWORK_DIR")
for _f in "${FONTES_EXTRAS[@]}"; do
  _f="${_f/#\~/$HOME}"; [[ -z "$_f" ]] && continue
  [[ -d "$_f/skills" || -d "$_f/agents" ]] || erro "fonte extra sem skills/ nem agents/: '$_f'"
  LIBS+=("$(cd "$_f" && pwd)")
done
declare -A FONTE_SKILL=() NOME_EM=()
CORE_SKILLS=(); EXTRA_SKILLS=()
for _lib in "${LIBS[@]}"; do
  [[ -d "$_lib/skills" ]] || continue
  while IFS= read -r _d; do
    _rel="${_d#"$_lib/skills/"}"; _base="$(basename "$_rel")"
    if [[ -n "${NOME_EM[$_base]:-}" ]]; then
      erro "skill '$_base' existe em duas fontes: ${NOME_EM[$_base]} e $_lib/skills/$_rel (nomes devem ser únicos — adaptador plano)"
    fi
    NOME_EM[$_base]="$_lib/skills/$_rel"; FONTE_SKILL[$_rel]="$_lib/skills"
    if [[ "$_rel" == */* ]]; then EXTRA_SKILLS+=("$_rel"); else CORE_SKILLS+=("$_rel"); fi
  done < <(find "$_lib/skills" -mindepth 2 -maxdepth 3 -name SKILL.md -printf '%h\n' | sort)
done
mapfile -t CORE_SKILLS < <(printf '%s\n' "${CORE_SKILLS[@]}" | sort)
mapfile -t EXTRA_SKILLS < <(printf '%s\n' "${EXTRA_SKILLS[@]}" | sort)
skill_dir() { printf '%s/%s' "${FONTE_SKILL[$1]}" "$1"; }
ALL_SKILLS=("${CORE_SKILLS[@]}" "${EXTRA_SKILLS[@]}")

# Resolve a seleção (padrão: só as de governança). Expande categoria/* e @padrao, e
# resolve nome sem caminho — possível porque nomes são únicos no acervo (adaptador plano).
resolve_skill() {
  local item="$1" achado
  if [[ "$item" == "@padrao" ]]; then printf '%s\n' "${CORE_SKILLS[@]}"; return; fi
  if [[ "$item" == */\* ]]; then
    achado="$(printf '%s\n' "${EXTRA_SKILLS[@]}" | awk -v c="${item%/\*}" 'index($0, c "/") == 1' || true)"
    [[ -n "$achado" ]] || erro "categoria vazia ou inexistente: '$item'"
    printf '%s\n' "$achado"; return
  fi
  if [[ -n "${FONTE_SKILL[$item]:-}" ]]; then printf '%s\n' "$item"; return; fi
  # comparação exata, não regex: '.' vindo do usuário não pode virar curinga (mockup.lab ≠ mockup-lab)
  achado="$(printf '%s\n' "${EXTRA_SKILLS[@]}" | awk -F/ -v n="$item" '$NF == n' || true)"
  [[ -n "$achado" ]] || erro "skill inexistente: '$item'. Veja skills/README.md (ou use categoria/*)."
  printf '%s\n' "$achado"
}
if [[ -n "$SKILLS_SELECTED" ]]; then
  IFS=',' read -r -a _itens <<< "$SKILLS_SELECTED"
  SKILLS=()
  for _i in "${_itens[@]}"; do
    _i="${_i// /}"; [[ -z "$_i" ]] && continue
    # $(...) e não < <(...): erro() dentro de substituição de processo encerra só o subshell,
    # e o nome inválido seria ignorado em silêncio.
    _res="$(resolve_skill "$_i")" || exit 1
    while IFS= read -r _r; do SKILLS+=("$_r"); done <<< "$_res"
  done
  mapfile -t SKILLS < <(printf '%s\n' "${SKILLS[@]}" | awk '!v[$0]++')
else
  SKILLS=("${CORE_SKILLS[@]}")
fi


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

# README da biblioteca: híbrido de texto (tem ilha para o catálogo local do projeto).
# O `rel` precisa ser qualificado com a pasta neutra — passar "README.md" cru o faria
# colidir com o README do projeto, que é `scaffold`, e a biblioteca nunca atualizaria.
install_file "$NEUTRAL_DIR/README.md" "$SKILLS_DIR/README.md" "$TARGET/$NEUTRAL_DIR/README.md"
for s in "${SKILLS[@]}"; do
  s="${s// /}"; [[ -z "$s" ]] && continue
  [[ -n "${FONTE_SKILL[$s]:-}" ]] || \
    erro "skill inexistente: '$s' (não há '$s/SKILL.md'). Disponíveis: ${ALL_SKILLS[*]}"
  # Artefatos de build/ambiente das skills executáveis nunca são instalados.
  while IFS= read -r -d '' f; do
    rel="${f#"${FONTE_SKILL[$s]}"/}"
    install_file "$NEUTRAL_DIR/$rel" "$f" "$TARGET/$NEUTRAL_DIR/$rel"
  done < <(find "$(skill_dir "$s")" -type f \
             -not -path '*/node_modules/*' -not -path '*/__pycache__/*' \
             -not -path '*/.venv/*' -not -name '*.pyc' -print0)
done
echo

# ----------------------------------------------------------------------------
# 2b) Subagents (pasta neutra agents/) e dependências entre skills
# ----------------------------------------------------------------------------
# Formato canônico: frontmatter do Claude Code (name, description, model, tools) — ADR 0013.
AGENTS=()
declare -A FONTE_AGENT=()
TODOS_AGENTS=()
for _lib in "${LIBS[@]}"; do
  [[ -d "$_lib/agents" ]] || continue
  while IFS= read -r _a; do
    [[ -n "${FONTE_AGENT[$_a]:-}" ]] && erro "subagent '$_a' existe em duas fontes: ${FONTE_AGENT[$_a]} e $_lib/agents"
    [[ -n "${NOME_EM[$_a]:-}" ]] && erro "subagent '$_a' tem o mesmo nome de uma skill (${NOME_EM[$_a]})"
    FONTE_AGENT[$_a]="$_lib/agents"; TODOS_AGENTS+=("$_a")
  done < <(find "$_lib/agents" -maxdepth 1 -name '*.md' -printf '%f\n' | sed 's/\.md$//')
done
mapfile -t TODOS_AGENTS < <(printf '%s\n' "${TODOS_AGENTS[@]}" | sed '/^$/d' | sort)
if [[ ${#TODOS_AGENTS[@]} -gt 0 && "$AGENTS_SELECTED" != "none" ]]; then
  case "$AGENTS_SELECTED" in
    all)  AGENTS=("${TODOS_AGENTS[@]}") ;;
    auto) # subagents citados pelo nome nas skills selecionadas
      for a in "${TODOS_AGENTS[@]}"; do
        for s in "${SKILLS[@]}"; do
          if grep -rqE -- "(^|[^a-z0-9-])${a}([^a-z0-9-]|$)" "$(skill_dir "$s")" 2>/dev/null; then AGENTS+=("$a"); break; fi
        done
      done ;;
    *)    IFS=',' read -r -a AGENTS <<< "$AGENTS_SELECTED"
          for a in "${AGENTS[@]}"; do [[ -n "${FONTE_AGENT[$a]:-}" ]] || erro "subagent inexistente: '$a'"; done ;;
  esac
fi
if [[ ${#AGENTS[@]} -gt 0 ]]; then
  info "2b) Subagents (pasta neutra: $AGENTS_NEUTRAL_DIR/, modo: $AGENTS_SELECTED) — ${#AGENTS[@]}"
  for a in "${AGENTS[@]}"; do
    install_file "$AGENTS_NEUTRAL_DIR/$a.md" "${FONTE_AGENT[$a]}/$a.md" "$TARGET/$AGENTS_NEUTRAL_DIR/$a.md"
  done
  echo
fi

# Dependências: skills citadas (skill `x`) pelas selecionadas e que ficaram de fora.
FALTANDO=()
for s in "${SKILLS[@]}"; do
  while IFS= read -r dep; do
    ok=0; for t in "${SKILLS[@]}"; do [[ "$(basename "$t")" == "$dep" ]] && { ok=1; break; }; done
    [[ $ok -eq 1 ]] && continue
    printf '%s\n' "${ALL_SKILLS[@]}" | awk -F/ -v n="$dep" '$NF == n {f=1} END {exit !f}' && FALTANDO+=("$dep")
  done < <(grep -rhoE 'skill `[a-z0-9-]+`' "$(skill_dir "$s")" 2>/dev/null | sed -E 's/skill `([a-z0-9-]+)`/\1/' | sort -u)
done
if [[ ${#FALTANDO[@]} -gt 0 ]]; then
  mapfile -t FALTANDO < <(printf '%s\n' "${FALTANDO[@]}" | sort -u)
  printf '\033[33maviso:\033[0m skills citadas pelas instaladas mas não selecionadas (%d): %s\n' \
    "${#FALTANDO[@]}" "$(printf '%s ' "${FALTANDO[@]}")"
  printf '  Acrescente-as a --skills (aceita o nome sem caminho) se for usar esses fluxos.\n\n'
fi

# ----------------------------------------------------------------------------
# 3) Gerar adaptadores do agente (ponteiros para a pasta neutra)
# ----------------------------------------------------------------------------
# Diretório de descoberta de cada harness. Claude Code lê de '.claude/skills';
# os demais convergiram para '.agents/skills' — caminho documentado pela OpenAI
# para skills locais do Codex, reconhecido nativamente por Gemini CLI e OpenCode,
# e alvo proposto para o agentry (ADR 0012).
adapter_dir_de() {
  case "$1" in
    claude) echo ".claude/skills" ;;
    *)      echo ".agents/skills" ;;
  esac
}

if [[ "$AGENT" != "none" && "$SKILLS_MODE" != "none" ]]; then
  IFS=',' read -r -a AGENTES <<< "$AGENT"
  # Vários harnesses compartilham '.agents/skills'; gera cada diretório uma vez só.
  DIRS_FEITOS=""
  for ag in "${AGENTES[@]}"; do
    ag="${ag// /}"; [[ -z "$ag" ]] && continue
    rel_dir="$(adapter_dir_de "$ag")"
    if [[ " $DIRS_FEITOS " == *" $rel_dir "* ]]; then
      info "3) $ag: compartilha '$rel_dir/' (já gerado)"
      continue
    fi
    DIRS_FEITOS="$DIRS_FEITOS $rel_dir"
    ADAPTER_DIR="$TARGET/$rel_dir"
    # profundidade do diretório do adaptador, para montar o '../' do symlink relativo
    niveis="$(awk -F/ '{print NF}' <<< "$rel_dir")"
    subir=""; for ((i=0;i<niveis;i++)); do subir="../$subir"; done
    info "3) Adaptador $ag em $rel_dir/ (modo: $SKILLS_MODE)"
    # Diretório de adaptador VAZIO é pior que ausente: harnesses que resolvem skills por
    # precedência de diretório (agentry, ADR-0047 dele) deixam de ler o de menor precedência.
    # Uma execução interrompida no meio pode deixá-lo assim — a limpeza abaixo evita isso.
    limpar_adapter_vazio() { [[ -d "$1" ]] && [[ -z "$(ls -A "$1" 2>/dev/null)" ]] && rmdir "$1"; return 0; }
    trap 'limpar_adapter_vazio "$ADAPTER_DIR"' EXIT
    for s in "${SKILLS[@]}"; do
      s="${s// /}"; [[ -z "$s" ]] && continue
      local_dst="$ADAPTER_DIR/$(basename "$s")"
      if [[ -e "$local_dst" && $FORCE -eq 0 && $UPDATE -eq 0 ]]; then
        printf '  pulado (já existe): %s\n' "$local_dst"; continue
      fi
      if [[ $DRY_RUN -eq 1 ]]; then
        printf '  [dry-run] %s -> %s\n' "$local_dst" "$SKILLS_MODE"; continue
      fi
      mkdir -p "$ADAPTER_DIR"
      rm -rf "$local_dst"
      if [[ "$SKILLS_MODE" == "symlink" ]]; then
        # O adaptador é sempre PLANO (harnesses descobrem skills em um só nível), então o
        # alvo pode ser aninhado ('dominio/mockup-lab') enquanto o link mantém só o basename.
        ln -s "${subir}$NEUTRAL_DIR/$s" "$local_dst"
        printf '  symlink: %s -> %s%s/%s\n' "$local_dst" "$subir" "$NEUTRAL_DIR" "$s"
      else
        cp -r "$(skill_dir "$s")" "$local_dst"
        printf '  cópia:   %s\n' "$local_dst"
      fi
    done
    limpar_adapter_vazio "$ADAPTER_DIR"; trap - EXIT
    echo
  done
  # Subagents: Claude Code por symlink (formato canônico = o dele); Codex e OpenCode
  # gerados por scripts/gerar-agent-adapter.py. Gemini e Copilot seguem pendentes (ADR 0013).
  if [[ ${#AGENTS[@]} -gt 0 ]]; then
    for ag in "${AGENTES[@]}"; do
      ag="${ag// /}"
      if [[ "$ag" == codex || "$ag" == opencode ]]; then
        # Gerados a partir do canônico (ADR 0013): cabeçalho traduzido, corpo idêntico.
        ADIR="$TARGET/.$ag/agents"
        info "3b) Subagents do $ag em .$ag/agents/ (gerados)"
        for a in "${AGENTS[@]}"; do
          if [[ $DRY_RUN -eq 1 ]]; then printf '  [dry-run] geraria %s/%s\n' "$ADIR" "$a"; continue; fi
          "$FRAMEWORK_DIR/scripts/gerar-agent-adapter.py" "$ag" "${FONTE_AGENT[$a]}/$a.md" "$ADIR" >/dev/null \
            || erro "falha ao gerar adaptador $ag do subagent '$a'"
        done
        printf '  %d subagent(s)\n\n' "${#AGENTS[@]}"
      elif [[ "$ag" == claude ]]; then
        ADIR="$TARGET/.claude/agents"
        info "3b) Subagents do Claude Code em .claude/agents/ (modo: $SKILLS_MODE)"
        for a in "${AGENTS[@]}"; do
          dst="$ADIR/$a.md"
          if [[ -e "$dst" && $FORCE -eq 0 && $UPDATE -eq 0 ]]; then printf '  pulado (já existe): %s\n' "$dst"; continue; fi
          if [[ $DRY_RUN -eq 1 ]]; then printf '  [dry-run] %s -> %s\n' "$dst" "$SKILLS_MODE"; continue; fi
          mkdir -p "$ADIR"; rm -f "$dst"
          if [[ "$SKILLS_MODE" == symlink ]]; then ln -s "../../$AGENTS_NEUTRAL_DIR/$a.md" "$dst"
          else cp "${FONTE_AGENT[$a]}/$a.md" "$dst"; fi
        done
        echo
      else
        PEND_AGENT_HARNESS+=("$ag")
      fi
    done
    if [[ ${#PEND_AGENT_HARNESS[@]} -gt 0 ]]; then
      printf '\033[33maviso:\033[0m subagents instalados em %s/, mas sem adaptador para: %s (ADR 0013, etapa posterior).\n\n' \
        "$AGENTS_NEUTRAL_DIR" "$(printf '%s ' "${PEND_AGENT_HARNESS[@]}")"
    fi
  fi
else
  info "3) Adaptador de agente desabilitado (skills disponíveis apenas na pasta neutra '$NEUTRAL_DIR/')."
  echo
fi

# ----------------------------------------------------------------------------
# Conclusão e próximos passos
# ----------------------------------------------------------------------------
# Armadilha de precedência: harness que resolve skills por diretório (agentry, ADR-0047 dele)
# usa '.agents/skills' quando ele EXISTE, mesmo vazio, e ignora '.claude/skills'.
for _d in .agents/skills .claude/skills; do
  if [[ -d "$TARGET/$_d" && -z "$(ls -A "$TARGET/$_d" 2>/dev/null)" ]]; then
    printf '\033[33maviso:\033[0m %s existe e está VAZIO em %s.\n' "$_d" "$TARGET"
    printf '  Harness que resolve por precedência de diretório pode deixar de ler o outro\n'
    printf '  adaptador por causa dele. Remova-o (rmdir) ou popule com --agent.\n\n'
  fi
done

if [[ ${#CONFLITOS[@]} -gt 0 ]]; then
  printf '\033[33mEdição local fora das ilhas em %d arquivo(s)\033[0m — originais preservados, versão nova em <arquivo>.new:\n' "${#CONFLITOS[@]}"
  printf '  - %s\n' "${CONFLITOS[@]}"
  printf '  Compare (diff -u arq arq.new), mova o que for do projeto para uma ilha USER, substitua\n'
  printf '  o arquivo pelo .new e rode --update de novo. Para descartar as edições locais: --force.\n\n'
fi
if [[ ${#SEM_BASELINE[@]} -gt 0 && $UPDATE -eq 1 ]]; then
  printf '\033[33mSem linha de base em %d arquivo(s)\033[0m (instalação anterior a este mecanismo):\n' "${#SEM_BASELINE[@]}"
  printf '  - %s\n' "${SEM_BASELINE[@]}"
  printf '  Não há como distinguir mudança do template de edição local: se havia texto editado\n'
  printf '  fora das ilhas, ele foi regenerado. Revise com "git diff" antes de commitar.\n'
  printf '  A linha de base foi gravada agora em %s — próximas atualizações ficam protegidas.\n\n' "$BASELINE_REL"
fi
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
