#!/usr/bin/env python3
# Caminho relativo: skills/dominio/transcrever-video/scripts/asr-local.py
"""Transcrição pelo caminho caro: baixa só o áudio e roda Whisper local (faster-whisper).

Para quando não há legenda — o caso comum em Facebook, Instagram, TikTok e áudio de WhatsApp.
Não precisa de ffmpeg no sistema: o áudio é decodificado pelo PyAV, que traz as próprias libs.
Usa GPU NVIDIA se houver (libs CUDA vêm dos wheels nvidia-*), senão CPU com modelo menor.

    uv run --no-project --with faster-whisper --with yt-dlp \\
        --with nvidia-cublas-cu12 --with "nvidia-cudnn-cu12==9.*" \\
        python asr-local.py <url-ou-arquivo> [--saida DIR] [--modelo large-v3-turbo] [--idioma pt]

Saídas em <saida> (padrão: .cache/transcricoes/, repo-local — ADR 0011):
    <id>.txt    texto com carimbo [mm:ss] por segmento; 1ª linha declara a origem (ASR, modelo, dispositivo)
    <id>.meta   título, autor, data, duração e URL (quando a entrada é URL)

Sem GPU, omita os dois --with nvidia-*. O áudio nunca sai da máquina.
"""
from __future__ import annotations

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path


def preparar_cuda() -> None:
    """Expõe as libs CUDA dos wheels nvidia-* e reexecuta (o loader lê LD_LIBRARY_PATH só no início)."""
    if os.environ.get("_ASR_LOCAL_REEXEC") == "1":
        return
    libs = [l for sp in sys.path for l in glob.glob(os.path.join(sp, "nvidia", "*", "lib"))]
    if not libs:
        return
    os.environ["LD_LIBRARY_PATH"] = ":".join(libs + [os.environ.get("LD_LIBRARY_PATH", "")])
    os.environ["_ASR_LOCAL_REEXEC"] = "1"
    os.execv(sys.executable, [sys.executable, *sys.argv])


def raiz_repo() -> Path:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:
        r = ""
    return Path(r) if r else Path(".")


def baixar_audio(url: str, destino: Path) -> tuple[Path, dict]:
    import yt_dlp  # dependência só do caminho por URL

    opts = {"format": "ba/b", "outtmpl": str(destino / "%(id)s.%(ext)s"), "quiet": True, "no_warnings": True, "noprogress": True}
    with yt_dlp.YoutubeDL(opts) as ydl:
        info = ydl.extract_info(url, download=True)
        caminho = Path(ydl.prepare_filename(info))
    meta = {k: info.get(k) for k in ("id", "title", "uploader", "upload_date", "duration", "webpage_url")}
    return caminho, meta


def decodificar(caminho: Path):
    import av
    import numpy as np

    rs = av.AudioResampler(format="s16", layout="mono", rate=16000)
    partes = []
    with av.open(str(caminho)) as c:
        for quadro in c.decode(audio=0):
            partes += [o.to_ndarray().reshape(-1) for o in rs.resample(quadro)]
        partes += [o.to_ndarray().reshape(-1) for o in rs.resample(None)]
    return np.concatenate(partes).astype(np.float32) / 32768.0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("entrada", help="URL do vídeo/áudio ou caminho de arquivo local")
    ap.add_argument("--saida", type=Path, default=None)
    ap.add_argument("--modelo", default="large-v3-turbo", help="modelo na GPU (CPU cai para 'small')")
    ap.add_argument("--idioma", default="pt")
    a = ap.parse_args()

    preparar_cuda()
    from faster_whisper import WhisperModel

    saida = a.saida or raiz_repo() / ".cache/transcricoes"
    saida.mkdir(parents=True, exist_ok=True)
    if Path(a.entrada).is_file():
        audio, meta = Path(a.entrada), {"id": Path(a.entrada).stem}
    else:
        audio, meta = baixar_audio(a.entrada, saida)

    try:
        modelo, disp = WhisperModel(a.modelo, device="cuda", compute_type="float16"), "cuda"
        nome = a.modelo
    except Exception as e:  # sem GPU ou sem libs CUDA: declara e segue em CPU
        print(f"GPU indisponível ({e}); usando CPU com 'small'", file=sys.stderr)
        modelo, disp, nome = WhisperModel("small", device="cpu", compute_type="int8"), "cpu", "small"

    segs, info = modelo.transcribe(decodificar(audio), language=a.idioma, vad_filter=True)
    txt = saida / f"{meta['id']}.txt"
    with txt.open("w", encoding="utf-8") as f:
        f.write(f"# origem: ASR local, faster-whisper {nome} ({disp}), idioma {info.language}\n")
        for s in segs:
            mm, ss = divmod(int(s.start), 60)
            f.write(f"[{mm:02d}:{ss:02d}] {s.text.strip()}\n")
    meta["origem"] = f"asr-local:{nome}:{disp}"
    (saida / f"{meta['id']}.meta").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
    print(txt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
