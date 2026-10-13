#!/usr/bin/env bash
# Caminho relativo: skills/pr-review-guard/scripts/checar-comando-git.sh
#
# Hook PreToolUse: recusa comando git do agente que altere estado local ou remoto. O agente
# PROPÕE o comando; quem executa é a pessoa.
#
# Existe porque a lista `deny` do settings.json casa por prefixo e por isso só pega a forma
# ingênua. Estas três passam pelo `deny` e são o mesmo comando:
#   git commit -m x            ← o deny pega
#   git -C /outro commit -m x  ← não pega: não começa com "git commit"
#   cd /outro && git commit    ← não pega: não começa com "git"
# Esta guarda olha a linha inteira, em qualquer posição, e é o mecanismo de verdade.
#
# Duas camadas de texto, por medição (2026-10-12):
#   precisa    — `git` ancorado em início de comando, com as opções globais entre o binário e
#                o verbo. Dá a mensagem específica e não recusa menção em argumento de leitura.
#   gananciosa — `git` + verbo mutante em QUALQUER posição de QUALQUER segmento da linha.
#                Fecha `sh -c '...'`, `/usr/bin/git`, `eval "..."`, `xargs ... git`, `env git`
#                e corpo de função — seis vetores que a camada precisa deixa passar, porque
#                neles o `git` vem precedido de aspa, barra ou nome de outro programa.
#                Aprendizado medido em guarda de terceiro (Matt Pocock, skills, MIT,
#                github.com/mattpocock/skills), cujo casamento é substring sem ancoragem.
#
# Nenhuma camada de texto fecha indireção que APAGA o texto: `bash deploy.sh`, `g=push; git $g`,
# `G=git; $G push`, `git pu"sh"`. O autoteste lista esses casos como lacuna conhecida, para que
# ninguém leia "autoteste passou" como "está coberto". Quem os fecha é o hook do próprio git
# (camada 1 do MT-24), que dispara em qualquer caminho de invocação.
#
# Uso como hook (settings.json, PreToolUse/Bash): recebe o JSON do evento em stdin.
#   Saída 0 = liberado. Saída 2 = recusado, com o motivo em stderr (o harness devolve ao modelo).
# Uso avulso:  checar-comando-git.sh --comando '<linha de comando>'
# Autoteste:   checar-comando-git.sh --autoteste
set -u

# Verbos que SEMPRE alteram estado: nenhuma forma de leitura vale a pena preservar.
VERBOS_MUTANTES='commit|push|merge|rebase|reset|revert|cherry-pick|stash|clean|am|apply|rm|mv|add|checkout|switch|restore|filter-branch|filter-repo|update-ref|fetch --prune|gc|prune|notes|replace|bisect'
# Verbos de uso misto: recusa só a forma que escreve, para não perder a leitura
# (`git branch --show-current`, `git tag -l`, `git remote -v`, `git config --get`).
MISTOS_MUTANTES='branch +(-(d|D|m|M|c|C|f)|[^-])|tag +(-(d|a|f|s)|[^-])|remote +(add|remove|rm|set-url|set-head|rename)|worktree +(add|remove|prune|move)|submodule +(add|update|deinit|sync)|config +(--(global|system|local|add|unset|replace-all)|[^-])'

# Ferramentas que só leem: `git commit` dentro dos argumentos delas é documentação, não
# execução. Sem esta ressalva a camada gananciosa recusa `grep -rn "git commit" docs/`.
FERRAMENTAS_LEITURA='grep|rg|ag|egrep|fgrep|echo|printf|cat|bat|less|more|head|tail|sed|awk|cut|sort|uniq|wc|jq|diff|find|ls|man|type|which|comm|tee|column'

recusa() {  # <linha> <motivo>
  printf 'Comando git recusado: %s\n' "$2" >&2
  printf '\n  %s\n\n' "$1" >&2
  cat >&2 <<'FIM'
Neste framework o agente NÃO executa git que altere estado local ou remoto. Ele propõe.
Devolva ao usuário:
  1. o que a mudança faz, em uma frase;
  2. o comando exato, em bloco de shell, pronto para colar;
  3. a mensagem de commit completa, quando for commit.
Leitura (status, log, diff, show, ls-files, branch --show-current) segue liberada.
FIM
  return 2
}

ganancioso() {  # <linha normalizada> -> 0 liberado, 2 recusado
  # Quebra a linha nos separadores de comando e avalia cada segmento por si: sem isso,
  # `echo origin | xargs -I{} git push {} main` seria dispensado pelo `echo` da frente.
  # A quebra não entende aspas, então `echo "a | git commit"` dá falso positivo — custo
  # aceito: menção a comando git com cano dentro da mesma aspa é raro, e recusa explica.
  local seg
  # `|| [[ -n "$seg" ]]`: sem isso o último segmento é descartado, porque não há \n final —
  # e é justamente o caso de linha sem separador, como `sh -c 'git push'`.
  while IFS= read -r seg || [[ -n "$seg" ]]; do
    [[ -z "${seg// /}" ]] && continue
    # Segmento que começa por ferramenta de leitura: a menção é argumento, não invocação.
    [[ "$seg" =~ ^[[:space:]]*(sudo[[:space:]]+)?($FERRAMENTAS_LEITURA)([[:space:]]|$) ]] && continue
    if [[ "$seg" =~ (^|[^A-Za-z0-9_-])git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*($VERBOS_MUTANTES)($|[[:space:]]) ]]; then
      return 2
    fi
    if [[ "$seg" =~ (^|[^A-Za-z0-9_-])git[[:space:]]+(-[^[:space:]]+[[:space:]]+)*($MISTOS_MUTANTES) ]]; then
      return 2
    fi
  done < <(printf '%s' "$1" | sed 's/&&/\n/g; s/||/\n/g; s/[;|`]/\n/g; s/\$(/\n/g; s/[(){}]/\n/g')
  return 0
}

avaliar() {  # <linha de comando> -> 0 liberado, 2 recusado
  local linha="$1"
  # Normaliza: colapsa espaço e remove continuação de linha, para `git  -C x   commit` casar.
  local n; n="$(printf '%s' "$linha" | tr '\n' ' ' | sed 's/\\ / /g; s/  */ /g')"
  # `git` em qualquer posição (início, depois de `&&`, `;`, `|`, `$(`, backtick), com as
  # opções globais (-C x, --git-dir=…, -c k=v) entre o `git` e o verbo.
  local pre='(^|[;&|(`]|&&|\|\||\$\() *(sudo +)?(env +[A-Za-z_]+=[^ ]* +)*git +((-C +[^ ]+|--git-dir=[^ ]+|--work-tree=[^ ]+|-c +[^ ]+|-c[^ ]+) +)*'
  if [[ "$n" =~ ${pre}($VERBOS_MUTANTES)($| ) ]]; then
    recusa "$linha" "altera estado local ou remoto"; return 2
  fi
  if [[ "$n" =~ ${pre}($MISTOS_MUTANTES) ]]; then
    recusa "$linha" "forma que escreve de um comando de uso misto"; return 2
  fi
  if ! ganancioso "$n"; then
    recusa "$linha" "indireção: comando git mutante aparece na linha fora de posição de comando"
    return 2
  fi
  return 0
}

if [[ "${1:-}" == "--autoteste" ]]; then
  falhas=0
  recusar=(
    'git commit -m "x"'
    'git -C /outro/repo commit -m "x"'
    'cd /outro/repo && git commit -m "x"'
    'git push origin main'
    'git  -c user.name=x  commit --amend'
    'git --git-dir=/a/.git --work-tree=/a reset --hard'
    'sudo git clean -fd'
    'git branch -D antiga'
    'git tag -d v1'
    'git remote set-url origin https://exemplo.invalid/x.git'
    'git config user.email a@b.c'
    'git submodule update --init'
    'git add -A'
    'git stash push -u -m x'
    'ls && git checkout main'
    'git worktree add ../w'
    'git branch nova'
    'git tag v1.2.3'
    # Indireção fechada pela camada gananciosa: o `git` não está em posição de comando.
    "sh -c 'git push origin main'"
    '/usr/bin/git push origin main'
    'eval "git push origin main"'
    'echo origin | xargs -I{} git push {} main'
    'env git push origin main'
    'f(){ git push origin main; }; f'
    'bash -lc "cd /x; git reset --hard"'
  )
  liberar=(
    'git status --short'
    'git log --oneline -5'
    'git diff --cached'
    'git show HEAD --stat'
    'git ls-files --others --exclude-standard'
    'git branch --show-current'
    'git branch -r'
    'git branch --list'
    'git tag -l'
    'git tag --list'
    'git remote -v'
    'git config --get user.name'
    'git -C /outro/repo status'
    'git rev-parse --show-toplevel'
    'grep -rn "git commit" docs/'
    'echo "rode git commit depois"'
    'rg "git push" skills/'
    'cat docs/regras/git.md'
    "sed -n '/git commit/p' README.md"
    'printf "git reset --hard\n"'
    'find . -name "*.sh" -newer README.md'
  )
  # Lacuna conhecida: indireção que APAGA o texto do comando. Nenhuma camada de texto fecha.
  # Quem fecha é o hook do próprio git (camada 1, MT-24). Listados para que "autoteste passou"
  # nunca seja lido como "está coberto".
  naocobertos=(
    'bash ./deploy.sh'
    'g=push; git $g origin main'
    'G=git; $G push origin main'
    'git pu"sh" origin main'
  )
  for c in "${recusar[@]}"; do
    if avaliar "$c" >/dev/null 2>&1; then
      printf '  \033[31mNÃO recusou:\033[0m %s\n' "$c" >&2; falhas=$((falhas+1))
    fi
  done
  for c in "${liberar[@]}"; do
    if ! avaliar "$c" >/dev/null 2>&1; then
      printf '  \033[31mrecusou indevidamente:\033[0m %s\n' "$c" >&2; falhas=$((falhas+1))
    fi
  done
  cobertos_agora=0
  for c in "${naocobertos[@]}"; do
    if ! avaliar "$c" >/dev/null 2>&1; then
      printf '  \033[33magora coberto (tire da lista de lacunas):\033[0m %s\n' "$c" >&2
      cobertos_agora=$((cobertos_agora+1))
    fi
  done
  if (( falhas )); then
    printf '\033[31mautoteste: %d caso(s) falharam\033[0m\n' "$falhas" >&2; exit 1
  fi
  printf '\033[32mautoteste: %d recusas e %d liberações, todas corretas\033[0m\n' \
    "${#recusar[@]}" "${#liberar[@]}"
  printf '\033[33mlacuna conhecida: %d forma(s) de indireção passam por desenho — texto do\033[0m\n' \
    "$(( ${#naocobertos[@]} - cobertos_agora ))"
  printf '\033[33mcomando ausente da linha. Fecha com hook do próprio git (camada 1, MT-24).\033[0m\n'
  exit 0
fi

if [[ "${1:-}" == "--comando" ]]; then
  avaliar "${2:-}"; exit $?
fi

# Modo hook: o evento chega em JSON no stdin. Sem python3, não dá para ler o campo com
# segurança — e guarda que falha aberta é pior que guarda ausente, então avisa e libera,
# em vez de bloquear todo Bash da sessão.
entrada="$(cat)"
if ! command -v python3 >/dev/null 2>&1; then
  printf 'checar-comando-git: python3 ausente; não consegui ler o evento — LIBERANDO\n' >&2
  exit 0
fi
cmd="$(printf '%s' "$entrada" | python3 -c '
import json, sys
try:
    d = json.load(sys.stdin)
except Exception:
    sys.exit(0)
print((d.get("tool_input") or {}).get("command", ""))
')"
[[ -z "$cmd" ]] && exit 0
avaliar "$cmd"
exit $?
