#!/usr/bin/env bash
# Caminho relativo: scripts/testar-instalador.sh
#
# Testes de regressão do setup-profile.sh, pelos casos que já doeram em campo.
# Cada caso é uma asserção de RECUSA ou de preservação — não de caminho feliz.
#
#   scripts/testar-instalador.sh
#
# Saída 0: todos passaram. 1: alguma asserção falhou. Não toca em repositório real.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
INSTALADOR="$AQUI/scripts/setup-profile.sh"
TMP="$(mktemp -d)"; trap 'rm -rf "$TMP"' EXIT
falhas=0

ok()    { printf '  \033[32m✓\033[0m %s\n' "$*"; }
falhou() { printf '  \033[31m✗\033[0m %s\n' "$*"; falhas=$((falhas+1)); }

repo() {  # repo <nome> -> cria repositório git vazio e ecoa o caminho
  local d="$TMP/$1"; mkdir -p "$d"
  git -C "$d" init -q
  git -C "$d" -c user.email=t@t -c user.name=t commit -q --allow-empty -m base
  printf '%s' "$d"
}

# --------------------------------------------------------------------------
# Caso 1 — arquivo de regra VERSIONADO pelo projeto não pode ser sobrescrito.
#
# Observado em uso real (2026-10-01): um CLAUDE.md de equipe, de 66 linhas e rastreado pelo
# git, foi substituído pelo ponteiro de 10 linhas. A linha de base não protegeu porque o
# arquivo nunca esteve nela — e a ausência de linha de base era lida como "instalação antiga".
# --------------------------------------------------------------------------
printf '\033[1mCaso 1\033[0m — arquivo de regra versionado pelo projeto\n'
alvo="$(repo rastreado)"
printf '# regras da equipe\n\nO agente PROPOE o comando git; o humano executa.\n' > "$alvo/CLAUDE.md"
git -C "$alvo" add CLAUDE.md
git -C "$alvo" -c user.email=t@t -c user.name=t commit -q -m "regra da equipe"
antes="$(sha256sum < "$alvo/CLAUDE.md")"

bash "$INSTALADOR" empresa "$alvo" --update >"$TMP/log1" 2>&1
saida=$?

[[ "$(sha256sum < "$alvo/CLAUDE.md")" == "$antes" ]] \
  && ok "CLAUDE.md rastreado ficou intacto" \
  || falhou "CLAUDE.md rastreado FOI ALTERADO — é o defeito de campo de volta"
[[ -f "$alvo/CLAUDE.md.new" ]] \
  && ok "versão do framework foi para CLAUDE.md.new" \
  || falhou "nenhum .new gravado: a versão nova se perdeu em silêncio"
grep -q "arquivo do PROJETO" "$TMP/log1" \
  && ok "o relatório destaca o arquivo preservado" \
  || falhou "o relatório não avisa que preservou arquivo do projeto"
[[ $saida -eq 0 ]] \
  && ok "o instalador terminou sem erro (preservar não é falha)" \
  || falhou "o instalador saiu com $saida"

# --------------------------------------------------------------------------
# Caso 2 — arquivo NÃO rastreado de instalação antiga continua sendo adotado.
# O remédio do caso 1 não pode paralisar a atualização legítima.
# --------------------------------------------------------------------------
printf '\033[1mCaso 2\033[0m — arquivo não rastreado de instalação anterior\n'
alvo2="$(repo solto)"
printf '# CLAUDE.md de instalação antiga\n' > "$alvo2/CLAUDE.md"
bash "$INSTALADOR" empresa "$alvo2" --update >"$TMP/log2" 2>&1

[[ ! -f "$alvo2/CLAUDE.md.new" ]] \
  && ok "nenhum .new para arquivo não rastreado" \
  || falhou ".new desnecessário: atualização legítima virou conflito"
grep -q "ai-coding-agent-profiles\|AGENTS.md" "$alvo2/CLAUDE.md" \
  && ok "o ponteiro do framework foi adotado" \
  || falhou "o arquivo não rastreado não foi atualizado"

# --------------------------------------------------------------------------
# Caso 3 — o hook commit-msg é instalado pelo próprio setup.
# Campo: a regra de proveniência existia em texto, e o hook era instalação manual que
# ninguém fazia — então o controle estrutural não existia onde mais importava.
# --------------------------------------------------------------------------
printf '\033[1mCaso 3\033[0m — hook commit-msg instalado pelo setup\n'
alvo3="$(repo com-hook)"
bash "$INSTALADOR" empresa "$alvo3" >"$TMP/log3" 2>&1
if [[ -e "$alvo3/.git/hooks/commit-msg" ]]; then
  ok "hook commit-msg presente"
  printf 'feat: x\n\nCo-authored-by: Alguem <a@b.c>\n' > "$TMP/msg"
  if "$alvo3/.git/hooks/commit-msg" "$TMP/msg" >/dev/null 2>&1; then
    falhou "o hook instalado NÃO recusa trailer proibido"
  else
    ok "o hook instalado recusa trailer proibido"
  fi
else
  falhou "setup-profile.sh não instalou o hook commit-msg"
fi

# --------------------------------------------------------------------------
# Caso 4 — a regra "o agente propõe git, a pessoa executa" chega instalada COM mecanismo.
#
# Regra escrita é o degrau mais fraco da escada de destinos. O que precisa chegar no projeto
# é o `deny` e o hook — e o hook tem de pegar as formas que o `deny` por prefixo não vê.
# --------------------------------------------------------------------------
printf '\033[1mCaso 4\033[0m — git somente-propor: regra, deny e hook\n'
alvo4="$(repo git-propor)"
bash "$INSTALADOR" empresa "$alvo4" >"$TMP/log4" 2>&1

grep -q 'o agente propõe, a pessoa executa' "$alvo4/AGENTS.md" \
  && ok "a regra está no AGENTS.md instalado" \
  || falhou "o AGENTS.md instalado não traz a regra"
grep -q '"Bash(git commit\*)"' "$alvo4/.claude/settings.json" \
  && ok "deny de git commit no settings.json" \
  || falhou "settings.json instalado sem o deny de git commit"
grep -q 'checar-comando-git.sh' "$alvo4/.claude/settings.json" \
  && ok "hook PreToolUse declarado no settings.json" \
  || falhou "settings.json instalado sem o hook"

hook4="$alvo4/skills/pr-review-guard/scripts/checar-comando-git.sh"
if [[ -e "$hook4" ]]; then
  ok "o script do hook chegou ao projeto"
  # O que o `deny` por prefixo NÃO pega, e é o motivo de o hook existir.
  for proibido in 'git commit -m x' 'git -C /outro commit -m x' 'cd /outro && git commit'; do
    if "$hook4" --comando "$proibido" >/dev/null 2>&1; then
      falhou "o hook NÃO recusou: $proibido"
    else
      ok "o hook recusou: $proibido"
    fi
  done
  "$hook4" --comando 'git status --short' >/dev/null 2>&1 \
    && ok "o hook libera leitura (git status)" \
    || falhou "o hook bloqueou leitura — falso positivo"
  "$hook4" --autoteste >/dev/null 2>&1 \
    && ok "autoteste do hook passa no projeto instalado" \
    || falhou "autoteste do hook falha no projeto instalado"
else
  falhou "o script do hook não chegou em $hook4"
fi

printf '\n'
if (( falhas )); then
  printf '\033[31m%d asserção(ões) falharam\033[0m\n' "$falhas"; exit 1
fi
printf '\033[32mtodas as asserções passaram\033[0m\n'
