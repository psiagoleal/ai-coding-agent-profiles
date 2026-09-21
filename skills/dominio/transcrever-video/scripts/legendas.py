#!/usr/bin/env python3
# Caminho relativo: skills/dominio/transcrever-video/scripts/legendas.py
"""Transcrição de vídeo pelo caminho barato: as legendas que a plataforma já tem.

Baixa a legenda (manual, se houver; automática, se não) com yt-dlp e converte em texto
corrido, sem ffmpeg, sem Whisper e sem baixar o vídeo. Segundos em vez de minutos.

    legendas.py <url> [--idiomas pt,en] [--saida DIR] [--manter-tempos]

Saídas em <saida> (padrão: .cache/transcricoes/, repo-local — ADR 0011):
    <id>.txt    texto corrido, pronto para leitura
    <id>.meta   título, canal, duração, idioma, origem da legenda

Sem legenda disponível, o script diz isso e sai com código 3 — aí, e só aí, vale o caminho
caro (baixar áudio e rodar ASR local). Ver SKILL.md.
"""
from __future__ import annotations

import argparse
import html
import json
import re
import subprocess
import sys
from pathlib import Path


def raiz_repo() -> Path:
    try:
        r = subprocess.run(["git", "rev-parse", "--show-toplevel"], capture_output=True, text=True).stdout.strip()
    except FileNotFoundError:  # sem git instalado (contêiner mínimo): cai no diretório corrente
        r = ""
    return Path(r) if r else Path(".")


def yt_dlp() -> list[str]:
    """yt-dlp do venv repo-local, do venv ativo ou do PATH — nesta ordem."""
    for cand in (raiz_repo() / ".cache/transcricoes/.venv/bin/yt-dlp", Path(sys.prefix) / "bin/yt-dlp"):
        if cand.is_file():
            return [str(cand)]
    if subprocess.run(["sh", "-c", "command -v yt-dlp"], capture_output=True).returncode == 0:
        return ["yt-dlp"]
    sys.exit("yt-dlp ausente. Instale num venv repo-local:\n"
             "  python3 -m venv .cache/transcricoes/.venv && .cache/transcricoes/.venv/bin/pip install -q yt-dlp")


def vtt_para_texto(vtt: str) -> str:
    """VTT → texto corrido, sem os carimbos de tempo nem a repetição de rolagem.

    Legenda automática reemite a última linha junto com a próxima, para simular rolagem; sem
    tratar isso, metade do texto sai duplicada.
    """
    linhas: list[str] = []
    for l in vtt.splitlines():
        if l.startswith(("WEBVTT", "Kind:", "Language:", "NOTE")) or "-->" in l or not l.strip():
            continue
        t = html.unescape(re.sub(r"<[^>]+>", "", l)).strip()
        if not t or (linhas and linhas[-1] == t):
            continue
        if linhas and (t.startswith(linhas[-1]) or linhas[-1].endswith(t)):
            linhas[-1] = max(t, linhas[-1], key=len)
        else:
            linhas.append(t)
    return re.sub(r"\s+", " ", " ".join(linhas)).strip()


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("url")
    ap.add_argument("--idiomas", default="", help="preferência, ex.: pt,en (padrão: o original do vídeo)")
    ap.add_argument("--saida", default="")
    ap.add_argument("--manter-tempos", action="store_true", help="grava também o .vtt bruto")
    a = ap.parse_args()

    saida = Path(a.saida) if a.saida else raiz_repo() / ".cache/transcricoes"
    saida.mkdir(parents=True, exist_ok=True)
    yd = yt_dlp()

    # JSON, não campos separados por tabulação: título com \t embaralharia todos os campos
    meta = subprocess.run(yd + ["--skip-download", "--dump-json", a.url], capture_output=True, text=True)
    if meta.returncode != 0 or not meta.stdout.strip():
        # a última linha de ERROR importa; o yt-dlp enche o stderr de WARNING irrelevante
        erros = [l for l in meta.stderr.splitlines() if l.strip() and not l.startswith("WARNING")]
        print(f"não consegui ler o vídeo: {(erros[-1] if erros else meta.stderr.strip())[:300]}", file=sys.stderr)
        return 1
    info = json.loads(meta.stdout.splitlines()[-1])
    vid, titulo = info.get("id", ""), info.get("title", "")
    canal, dur = info.get("channel") or info.get("uploader", ""), info.get("duration_string", "")
    idioma = info.get("language") or ""

    prefs = [x for x in a.idiomas.split(",") if x]
    base = idioma.split("-")[0] if idioma else ""
    # Ordem de preferência EXPLÍCITA — é ela que decide a escolha, não a ordem alfabética dos
    # arquivos (com sorted(), "en" venceria "pt" num vídeo em português).
    ordem = [x for x in dict.fromkeys(
        [c for p in prefs for c in (f"{p}-orig", p)] + [f"{base}-orig", base, idioma, "en-orig", "en"]) if x]

    def limpar():  # legenda de execução anterior contaminaria a escolha e seria apagada no fim
        for v in saida.glob(f"{vid}.*.vtt"):
            v.unlink()

    limpar()
    achados, origem, falhas = [], "", []
    # legenda manual primeiro: quando existe, é revisada por gente e vale mais que a automática
    for flags, rotulo in ((["--write-subs"], "manual"), (["--write-subs", "--write-auto-subs"], "automática")):
        r = subprocess.run(yd + ["--skip-download", *flags, "--sub-langs", ",".join(ordem), "--sub-format", "vtt",
                                 "-o", str(saida / "%(id)s.%(ext)s"), a.url], capture_output=True, text=True)
        if r.returncode != 0:
            falhas.append(r.stderr)
        baixados = {v.name[len(vid) + 1:-4]: v for v in saida.glob(f"{vid}.*.vtt")}
        escolhido = next((baixados[l] for l in ordem if l in baixados), None) or \
                    (sorted(baixados.values())[0] if baixados else None)
        if escolhido:
            achados, origem = [escolhido], rotulo
            break

    if not achados:
        if falhas and all("ERROR" in f for f in falhas):
            erro = [l for l in falhas[-1].splitlines() if l.startswith("ERROR")]
            print(f"falha ao baixar legenda (não é ausência de legenda): {(erro or ['?'])[-1][:300]}",
                  file=sys.stderr)
            return 1  # rede ou bloqueio: NÃO mandar para o caminho caro de ASR por engano
        print(f"'{titulo}' não tem legenda disponível — use o caminho de ASR local (ver SKILL.md).", file=sys.stderr)
        return 3

    escolhida = achados[0]
    texto = vtt_para_texto(escolhida.read_text(encoding="utf-8", errors="replace"))
    (saida / f"{vid}.txt").write_text(texto + "\n", encoding="utf-8")
    (saida / f"{vid}.meta").write_text(json.dumps(
        {"id": vid, "titulo": titulo, "canal": canal, "duracao": dur, "idioma_video": idioma,
         "legenda": escolhida.name, "origem": origem, "palavras": len(texto.split()), "url": a.url},
        ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    if not a.manter_tempos:
        limpar()
    print(f"{saida / (vid + '.txt')}  ({len(texto.split())} palavras, legenda {origem}: {titulo})")
    return 0


if __name__ == "__main__":
    sys.exit(main())
