#!/usr/bin/env bash
# Caminho relativo: skills/delegacao-openai-compat/scripts/testar-oa-chat.sh
#
# Autoteste do oa-chat contra um endpoint FABRICADO em 127.0.0.1: sem rede, sem credencial.
# Cada "modelo" do servidor falso reproduz um comportamento medido em endpoint real
# (2026-10-29): recusar a chave `thinking` nomeando-a (LiteLLM + Ollama), recusar sem nomear,
# truncar raciocinando, obedecer só ao template, vazar o raciocínio para o conteúdo.
#
# Uso: testar-oa-chat.sh        Saída 0 = todos os casos corretos.
set -uo pipefail

AQUI="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
OA="$AQUI/oa-chat"
tmp="$(mktemp -d)"; trap 'kill "${pid:-}" 2>/dev/null; rm -rf "$tmp"' EXIT

cat > "$tmp/servidor.py" <<'PY'
import json, sys
from http.server import BaseHTTPRequestHandler, HTTPServer
LOG = sys.argv[1]

def resposta(conteudo, saida, fim="stop"):
    return 200, {"choices": [{"message": {"content": conteudo}, "finish_reason": fim}],
                 "usage": {"prompt_tokens": 10, "completion_tokens": saida}}

class H(BaseHTTPRequestHandler):
    def log_message(self, *a): pass
    def do_POST(self):
        corpo = json.loads(self.rfile.read(int(self.headers["Content-Length"])))
        with open(LOG, "a") as f: f.write(json.dumps(corpo) + "\n")
        m = corpo.get("model")
        template = (corpo.get("chat_template_kwargs") or {}).get("enable_thinking") is False
        thinking = (corpo.get("thinking") or {}).get("type") == "disabled"
        if m == "eco":
            code, r = resposta(json.dumps(sorted(corpo)), 5)
        elif m == "recusa-thinking" and "thinking" in corpo:
            code, r = 400, {"error": {"message": "UnsupportedParamsError: does not support parameters: ['thinking']"}}
        elif m == "recusa-thinking":
            code, r = resposta("OK", 2)
        elif m == "recusa-generica":
            code, r = 400, {"error": {"message": "bad request"}}
        elif m == "trunca":
            code, r = resposta("", corpo["max_tokens"], "length")
        elif m == "obedece-template":
            code, r = resposta("OK", 2) if template else resposta("OK", 300)
        elif m == "vaza":
            code, r = resposta("The user is asking me to answer OK.\nOK", 90) if (template or thinking) else resposta("OK", 300)
        else:
            code, r = 404, {"error": {"message": "modelo desconhecido"}}
        dados = json.dumps(r).encode()
        self.send_response(code); self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(dados))); self.end_headers(); self.wfile.write(dados)

srv = HTTPServer(("127.0.0.1", 0), H)
print(srv.server_address[1], flush=True)
srv.serve_forever()
PY

python3 -I "$tmp/servidor.py" "$tmp/log" > "$tmp/porta" 2>/dev/null &
pid=$!
for _ in $(seq 50); do [[ -s "$tmp/porta" ]] && break; sleep 0.1; done
[[ -s "$tmp/porta" ]] || { echo "servidor falso não subiu" >&2; exit 1; }

# Nenhuma credencial real chega ao servidor falso.
unset OPENAI_COMPAT_API_KEY OPENAI_COMPAT_KEY_CMD OPENAI_COMPAT_KEY_FILE OPENAI_COMPAT_MODEL \
      AGENTRY_LITELLM_API_KEY AGENTRY_LITELLM_BASE_URL
export OPENAI_COMPAT_BASE_URL="http://127.0.0.1:$(cat "$tmp/porta")"

falhas=0; casos=0
confere() {  # <descrição> <condição bash>
  casos=$((casos+1))
  if eval "$2"; then printf '  \033[32mok\033[0m    %s\n' "$1"
  else printf '  \033[31mFALHA\033[0m %s\n' "$1"; falhas=$((falhas+1)); fi
}
roda() {  # args... → $rc, $tmp/out, $tmp/err; zera o log antes
  : > "$tmp/log"
  "$OA" "$@" > "$tmp/out" 2> "$tmp/err"; rc=$?
}
pedidos() { wc -l < "$tmp/log"; }
corpo() { sed -n "${1}p" "$tmp/log"; }

roda -m eco --no-think "x"
confere "--no-think manda as duas chaves na primeira tentativa" \
  '[[ $rc -eq 0 ]] && corpo 1 | jq -e ".chat_template_kwargs.enable_thinking == false and .thinking.type == \"disabled\"" >/dev/null'

roda -m recusa-thinking --no-think "x"
confere "endpoint recusa thinking nomeando-a: repete sem ela, mantém a outra, avisa" \
  '[[ $rc -eq 0 && $(pedidos) -eq 2 ]] && ! corpo 2 | jq -e "has(\"thinking\")" >/dev/null && corpo 2 | jq -e ".chat_template_kwargs.enable_thinking == false" >/dev/null && grep -q "recusou .thinking." "$tmp/err"'

roda -m recusa-thinking --extra '{"thinking":{"type":"disabled"}}' "x"
confere "chave pedida em --extra nunca é retirada: uma tentativa, erro" \
  '[[ $rc -eq 1 && $(pedidos) -eq 1 ]]'

roda -m recusa-generica --no-think "x"
confere "4xx que não nomeia chave do --no-think: sem nova tentativa" \
  '[[ $rc -eq 1 && $(pedidos) -eq 1 ]]'

roda -m trunca --max-tokens 50 "x"
confere "resposta vazia por length sai com 3 e aponta a sonda" \
  '[[ $rc -eq 3 ]] && grep -q -- "--sonda-think" "$tmp/err"'

roda -m eco "x"
confere "sem --no-think, nenhuma das duas chaves vai no corpo" \
  '[[ $rc -eq 0 ]] && ! corpo 1 | jq -e "has(\"thinking\") or has(\"chat_template_kwargs\")" >/dev/null'

roda --sonda-think -m obedece-template
confere "sonda: template desliga 3/3 e --no-think é recomendado" \
  '[[ $rc -eq 0 ]] && grep -qE "^  template +3 " "$tmp/out" && grep -q -- "--no-think funciona" "$tmp/out"'

roda --sonda-think -m vaza
confere "sonda: vazamento classificado como vazou, e nenhuma chave recomendada" \
  '[[ $rc -eq 0 ]] && grep -qE "^  no-think +0 +0 +3 " "$tmp/out" && grep -q "nenhuma chave desligou" "$tmp/out"'

roda --sonda-think -m recusa-thinking
confere "sonda: thinking recusado 3/3, e o --no-think desliga pelo recuo" \
  '[[ $rc -eq 0 ]] && grep -qE "^  thinking +0 +0 +0 +0 +3 " "$tmp/out" && grep -qE "^  no-think +3 " "$tmp/out"'

if (( falhas )); then
  printf '\033[31mautoteste do oa-chat: %d de %d casos falharam\033[0m\n' "$falhas" "$casos"; exit 1
fi
printf '\033[32mautoteste do oa-chat: %d casos corretos\033[0m\n' "$casos"
echo "não examinado: endpoint real (o comportamento de cada implantação só a --sonda-think mede), streaming, chamada de ferramenta"
