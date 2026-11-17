# Uso: source skills/dominio/apresentacao-html/scripts/ambiente.sh
# Aponta caches e configuração de ferramentas para dentro da skill (ADR 0011
# do acervo: nada em diretório do usuário). Depois, use `py` para rodar Python
# com as bibliotecas de figura sem instalar nada no sistema.
_SKILL="$(cd "$(dirname "${BASH_SOURCE[0]:-${(%):-%x}}")/.." && pwd)"
export APRESENTACAO_SKILL="$_SKILL"
export UV_CACHE_DIR="$_SKILL/.cache/uv"
export UV_PYTHON_INSTALL_DIR="$_SKILL/.cache/uv-python"
export npm_config_cache="$_SKILL/.cache/npm"
export PLAYWRIGHT_BROWSERS_PATH="$_SKILL/.cache/ms-playwright"
export MPLCONFIGDIR="$_SKILL/.cache/matplotlib"
export XDG_CACHE_HOME="$_SKILL/.cache/xdg-cache"
export XDG_CONFIG_HOME="$_SKILL/.cache/xdg-config"
mkdir -p "$UV_CACHE_DIR" "$MPLCONFIGDIR" "$XDG_CACHE_HOME" "$XDG_CONFIG_HOME"

# py <script.py> [args]: Python 3.12 isolado com matplotlib, schemdraw e imageio-ffmpeg.
py() {
  uv run --no-project --python 3.12 \
    --with "matplotlib==3.9.4" --with "schemdraw==0.19" --with "imageio-ffmpeg==0.5.1" \
    python -I "$@"
}
