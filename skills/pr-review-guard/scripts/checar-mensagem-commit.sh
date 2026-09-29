#!/usr/bin/env bash
# Caminho relativo: skills/pr-review-guard/scripts/checar-mensagem-commit.sh
#
# Hook commit-msg: recusa a mensagem de commit que traga qualquer entrada de agente além do
# marcador entre chaves ({agente: ...; modelo: ...}) — link ou ID de sessão, URL de conversa,
# rodapé "Generated with…", trailers Co-authored-by/Assisted-by/Generated-by/*-Session.
#
# Existe porque a regra em texto (seção de proveniência do AGENTS.md) é probabilística: a
# ferramenta pode acrescentar essas linhas por padrão, e o agente segue a ferramenta.
#
# Instalação no clone (local, não versionada):
#   ln -sf ../../skills/pr-review-guard/scripts/checar-mensagem-commit.sh .git/hooks/commit-msg
# Uso avulso: skills/pr-review-guard/scripts/checar-mensagem-commit.sh <arquivo-com-a-mensagem>
# Autoteste:   skills/pr-review-guard/scripts/checar-mensagem-commit.sh --autoteste
#
# ⚠️ Instalado como symlink, este arquivo É o hook: redirecionamento de shell
# (`cat > .git/hooks/commit-msg`) segue o link e sobrescreve ESTE script. Use `rm -f` no link
# antes de pôr outra coisa no lugar.
set -u

# Guarda que não prova que detecta é decoração. O autoteste roda os casos proibidos e um
# limpo, e é o que entra no CI.
if [[ "${1:-}" == "--autoteste" ]]; then
  t="$(mktemp -d)"; trap 'rm -rf "$t"' EXIT
  falhas=0
  esperado_recusa=(
    "Claude-Session: https://exemplo.invalid/code/session_AbC123"
    "Co-authored-by: Fulano <f@exemplo.invalid>"
    "Generated with [Ferramenta](https://claude.ai/code)"
    "Assisted-by: Gemini"
    "veja https://chatgpt.com/share/xyz"
  )
  for linha in "${esperado_recusa[@]}"; do
    printf 'feat: algo\n\ncorpo\n\n%s\n' "$linha" > "$t/m"
    if "$0" "$t/m" >/dev/null 2>&1; then
      printf '  \033[31mNÃO detectou:\033[0m %s\n' "$linha" >&2; falhas=$((falhas+1))
    fi
  done
  # Limpo, incluindo o marcador permitido e a palavra "sessão" em prosa.
  printf 'feat: algo\n\nRevisado na sessão de hoje.\n\n{agente: X; modelo: y}\n' > "$t/m"
  if ! "$0" "$t/m" >/dev/null 2>&1; then
    printf '  \033[31mfalso positivo\033[0m em mensagem limpa\n' >&2; falhas=$((falhas+1))
  fi
  if (( falhas )); then
    printf 'autoteste: %d falha(s)\n' "$falhas" >&2; exit 1
  fi
  printf 'autoteste: %d caso(s) de recusa e 1 limpo, todos corretos\n' "${#esperado_recusa[@]}"
  exit 0
fi

msg="${1:?uso: checar-mensagem-commit.sh <arquivo-da-mensagem>}"
# ignora comentários do editor (linhas iniciadas por #)
corpo="$(grep -v '^#' "$msg")"
padrao='(claude\.ai/code|chatgpt\.com/(c|share)/|/session[_-][A-Za-z0-9]+|[A-Za-z]+-Session:|^(Co-authored-by|Assisted-by|Generated-by):|Generated with \[?(Claude|Codex|Copilot|Gemini|Cursor))'
achados="$(printf '%s\n' "$corpo" | grep -niE "$padrao" || true)"
if [[ -n "$achados" ]]; then
  printf '\033[31mcommit-msg:\033[0m a mensagem tem entrada de agente além do marcador entre chaves:\n' >&2
  printf '%s\n' "$achados" | sed 's/^/  linha /' >&2
  printf '  Único registro permitido: {agente: <nome>; modelo: <modelo/versão>} ao final.\n' >&2
  exit 1
fi
exit 0
