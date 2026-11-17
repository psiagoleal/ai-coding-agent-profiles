"""Converte gravação de tela em GIF ou vídeo leve para o deck. Usa o ffmpeg estático
do pacote imageio-ffmpeg (não depende de ffmpeg no sistema).

Uso (depois de `source scripts/ambiente.sh`):
  py scripts/gif.py entrada.webm saida.gif [--fps 12] [--largura 960] [--inicio 2] [--duracao 8]
  py scripts/gif.py entrada.webm saida.mp4 [--crf 28]          # H.264, toca em qualquer navegador
  py scripts/gif.py entrada.webm saida.webm [--crf 36]         # VP9, menor
  py scripts/gif.py --de-imagens "pasta/slide-*.png" saida.gif --segundos 2

GIF: paleta própria por vídeo (palettegen/paletteuse), loop infinito. Para mais de
~10 s ou tela grande, prefira mp4 com <video autoplay loop muted playsinline>.
"""

from __future__ import annotations

import argparse
import glob
import subprocess
import sys
from pathlib import Path

import imageio_ffmpeg


def rodar(args: list[str]) -> None:
    cmd = [imageio_ffmpeg.get_ffmpeg_exe(), "-hide_banner", "-loglevel", "error", "-y", *args]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        sys.exit(f"ERRO ffmpeg: {r.stderr.strip()[:600]}")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", nargs="?")
    ap.add_argument("saida", type=Path)
    ap.add_argument("--de-imagens", help='padrão glob de imagens, ex.: "pasta/slide-*.png"')
    ap.add_argument("--segundos", type=float, default=2.0, help="duração de cada imagem em --de-imagens")
    ap.add_argument("--fps", type=int, default=12)
    ap.add_argument("--largura", type=int, default=960)
    ap.add_argument("--inicio", type=float)
    ap.add_argument("--duracao", type=float)
    ap.add_argument("--crf", type=int)
    a = ap.parse_args()

    if a.de_imagens:
        imagens = sorted(glob.glob(a.de_imagens))
        if not imagens:
            sys.exit(f"ERRO nenhuma imagem casa com {a.de_imagens}")
        lista = a.saida.with_suffix(".lista.txt")
        linhas = [f"file '{Path(i).resolve()}'\nduration {a.segundos}" for i in imagens]
        lista.write_text("\n".join(linhas) + f"\nfile '{Path(imagens[-1]).resolve()}'\n", encoding="utf-8")
        entrada = ["-f", "concat", "-safe", "0", "-i", str(lista)]
        fps = 10
    elif a.entrada:
        entrada = []
        if a.inicio is not None:
            entrada += ["-ss", str(a.inicio)]
        if a.duracao is not None:
            entrada += ["-t", str(a.duracao)]
        entrada += ["-i", a.entrada]
        fps = a.fps
    else:
        sys.exit("ERRO informe a entrada ou --de-imagens")

    escala = f"scale={a.largura}:-2:flags=lanczos"
    a.saida.parent.mkdir(parents=True, exist_ok=True)
    sufixo = a.saida.suffix.lower()
    if sufixo == ".gif":
        filtro = f"fps={fps},{escala},split[a][b];[a]palettegen=stats_mode=diff[p];[b][p]paletteuse=dither=bayer:bayer_scale=5:diff_mode=rectangle"
        rodar([*entrada, "-vf", filtro, "-loop", "0", str(a.saida)])
    elif sufixo == ".mp4":
        rodar([*entrada, "-vf", f"fps={max(fps, 25) if a.de_imagens else fps},{escala}", "-c:v", "libx264", "-crf", str(a.crf or 28),
               "-preset", "slow", "-pix_fmt", "yuv420p", "-movflags", "+faststart", "-an", str(a.saida)])
    elif sufixo == ".webm":
        rodar([*entrada, "-vf", f"fps={max(fps, 25) if a.de_imagens else fps},{escala}", "-c:v", "libvpx-vp9", "-crf", str(a.crf or 36),
               "-b:v", "0", "-an", str(a.saida)])
    else:
        sys.exit("ERRO saída deve ser .gif, .mp4 ou .webm")
    if a.de_imagens:
        lista.unlink(missing_ok=True)
    kb = a.saida.stat().st_size / 1024
    print(f"gerado {a.saida} ({kb:.0f} KB)")
    if kb > 5 * 1024:
        print("AVISO acima de 5 MB: reduza --largura, --fps ou --duracao, ou use .mp4")
    print("MIDIA OK")


if __name__ == "__main__":
    main()
