#!/usr/bin/env python3
"""Converte PDF em Markdown pelo serviço docling local, com procedência.

Uso:
    uv run --with pikepdf --with requests python3 pdf2md.py ENTRADA.pdf \
        --out base/refs/NOME.md \
        [--paginas 12,22,31] [--strip-regex "Customer: .*"] \
        [--sem-figuras] [--sem-formulas] [--html] [--remove-blocos] \
        [--url http://localhost:8010] [--dpi 150]

O que o script resolve, e que custa caro redescobrir:

  * **`format=json` descarta as figuras.** O serviço materializa as imagens num
    diretório temporário, referencia todas no Markdown e apaga o diretório ao
    responder — devolvendo um campo `assets_dir` que aponta para o nada. O
    resultado é um `.md` com dezenas de links quebrados. Aqui pedimos
    `format=zip`, que traz Markdown e imagens, e reescrevemos os caminhos para a
    pasta local de assets.
  * **PDF cifrado devolve HTTP 500.** O docling não abre o arquivo e a mensagem
    (`Nenhum arquivo .md gerado`) não diz o motivo — a mesma mensagem cobre OOM de
    VRAM e falha de pipeline. Aqui o PDF é decifrado com `pikepdf` antes do envio,
    sempre que vier cifrado.
  * **Descrever figuras mais que dobra o tempo** e vem ligado por padrão na API.
    Medido em 71 páginas A4 numa RTX 3070: 37 s com fórmulas, 77 s somando a
    descrição de figuras. Use `--sem-figuras` quando só o texto importa.
  * **O VLM padrão do serviço descreve genericamente.** Este script pede
    `smolvlm-500m`, que lê rótulos de diagramas e cabe na mesma VRAM; o `granite`
    in-process não cabe em 8 GB. Ver `--modelo-figuras`.
  * **`enhance` fica desligado, sempre.** No golden do serviço o pós-processamento
    por LLM não melhora o placar e corrompe conteúdo factual — reescreveu "Mercúrio"
    como "Mercuryo". Numa extração destinada a citação, alteração silenciosa e
    plausível é o pior defeito possível.
  * **`remove_headers_footers` é inócuo sozinho.** Exige `enhance=true` e um
    `vision_provider`, apesar de vir `true` por padrão. Para rodapé repetido, use
    `--remove-blocos` (regex por contagem, sem LLM) ou `--strip-regex`.
"""

from __future__ import annotations

import argparse
import io
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from datetime import date
from pathlib import Path


def erro(msg: str) -> None:
    print(f"erro: {msg}", file=sys.stderr)
    raise SystemExit(1)


def triagem(pdf: Path) -> dict:
    """Levanta páginas, cifra e se o PDF tem camada de texto."""
    import pikepdf

    info: dict = {"cifrado": False, "paginas": 0, "tem_texto": None}
    try:
        with pikepdf.open(pdf) as doc:
            info["paginas"] = len(doc.pages)
            info["cifrado"] = doc.is_encrypted
    except pikepdf.PasswordError:
        erro(f"{pdf} exige senha. Abra com `pikepdf.open(pdf, password=...)`.")

    if shutil.which("pdftotext"):
        amostra = subprocess.run(
            ["pdftotext", "-f", "1", "-l", "3", str(pdf), "-"],
            capture_output=True, text=True,
        ).stdout
        info["tem_texto"] = len(amostra.split()) > 40
    return info


def decifrar(pdf: Path, destino: Path) -> Path:
    """Reescreve o PDF sem cifra. Sem isso o docling devolve HTTP 500."""
    import pikepdf

    with pikepdf.open(pdf) as doc:
        doc.save(destino)
    return destino


def converter(pdf: Path, url: str, timeout: int, params: dict) -> tuple[bytes, float]:
    """Pede `format=zip` — é o único modo que devolve as imagens."""
    import requests

    inicio = time.monotonic()
    with pdf.open("rb") as fh:
        resp = requests.post(
            f"{url.rstrip('/')}/convert",
            params={"format": "zip", **params},
            files={"file": (pdf.name, fh, "application/pdf")},
            timeout=timeout,
        )
    decorrido = time.monotonic() - inicio

    if resp.status_code != 200:
        # Serviço atualizado devolve a causa real em `detail`/`type` e, quando a
        # reconhece, um `hint` acionável. Versões antigas só trazem `error`.
        linhas = [f"docling devolveu HTTP {resp.status_code} em {decorrido:.0f}s"]
        try:
            corpo = resp.json()
        except ValueError:
            corpo = {}
        if corpo.get("detail"):
            linhas.append(f"       causa: {corpo.get('type', 'erro')}: {corpo['detail']}")
        else:
            linhas.append(f"       {resp.text[:300]}")
            linhas.append(
                "       O serviço não informou a causa (versão antiga): veja"
                " `docker compose logs docling`."
            )
        if corpo.get("hint"):
            linhas.append(f"       saída: {corpo['hint']}")
        erro("\n".join(linhas))

    return resp.content, decorrido


def desempacotar(blob: bytes, destino_md: Path, ext: str) -> tuple[str, Path | None]:
    """Extrai o zip: devolve o texto e materializa os assets ao lado do .md.

    O zip traz `<stem>.<ext>` e, quando há figuras, `<stem>_assets/`. Como o
    destino costuma ter outro nome, a pasta é renomeada e as referências dentro do
    documento são reescritas — senão os links quebram silenciosamente.
    """
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        nomes = z.namelist()
        docs = [n for n in nomes if n.lower().endswith(f".{ext}")]
        if not docs:
            erro(f"zip do docling não contém nenhum .{ext} (conteúdo: {nomes[:5]})")
        doc_nome = docs[0]
        texto = z.read(doc_nome).decode("utf-8")

        origem_assets = f"{Path(doc_nome).stem}_assets"
        arquivos = [n for n in nomes if n.startswith(f"{origem_assets}/") and not n.endswith("/")]
        if not arquivos:
            return texto, None

        destino_assets = destino_md.with_name(f"{destino_md.stem}_assets")
        if destino_assets.exists():
            shutil.rmtree(destino_assets)
        destino_assets.mkdir(parents=True, exist_ok=True)
        for nome in arquivos:
            (destino_assets / Path(nome).name).write_bytes(z.read(nome))

    texto = texto.replace(f"{origem_assets}/", f"{destino_assets.name}/")
    return texto, destino_assets


def extrair_paginas(pdf: Path, paginas: list[int], destino: Path, dpi: int) -> list[Path]:
    """Renderiza páginas inteiras — para conferir número contra o original.

    Complementa `_assets/` (figuras recortadas pelo docling): aqui vem a página
    com eixos, legenda e contexto, que é o que sustenta uma conferência.
    """
    if not shutil.which("pdftoppm"):
        print("aviso: pdftoppm ausente; páginas não extraídas", file=sys.stderr)
        return []
    destino.mkdir(parents=True, exist_ok=True)
    geradas = []
    for p in paginas:
        subprocess.run(
            ["pdftoppm", "-png", "-r", str(dpi), "-f", str(p), "-l", str(p),
             str(pdf), str(destino / "pag")],
            check=True, capture_output=True,
        )
        for f in destino.glob("pag-*.png"):
            n = int(re.findall(r"(\d+)", f.name)[-1])
            alvo = destino / f"pag-{n:03d}.png"
            if f != alvo:
                f.rename(alvo)
            geradas.append(alvo)
    return sorted(set(geradas))


def itens_procedencia(origem: Path, info: dict, ctx: dict) -> list[str]:
    """As dívidas da extração, em markdown inline. Formatadas depois por formato."""
    itens = [
        f"**Origem:** `{origem}` ({info['paginas']} páginas"
        + (", PDF cifrado" if info["cifrado"] else "")
        + (", sem camada de texto — provável digitalização" if info["tem_texto"] is False else "")
        + ").",
        "**Extração:** "
        + ("decifrado com `pikepdf`, " if info["cifrado"] else "")
        + f"convertido pelo serviço docling local em {ctx['segundos']:.0f}s, "
        + f"{date.today().isoformat()}.",
        f"**Flags:** {ctx['flags']}.",
    ]
    if ctx["formulas"]:
        itens.append(
            "✅ **O docling preserva índices, expoentes e letras gregas**, entregando "
            "equações em LaTeX — é a razão de usá-lo no lugar de `pdftotext`, que "
            "corrompe esses símbolos."
        )
    else:
        itens.append(
            "⚠️ **Enriquecimento de fórmulas desligado** nesta extração: as equações "
            "**não** estão em LaTeX semântico. Não cite equação a partir deste arquivo."
        )
    if ctx["assets"]:
        itens.append(
            f"🖼️ **{ctx['n_assets']} figuras** extraídas em "
            f"[`{ctx['assets'].name}/`]({ctx['assets'].name}/)."
        )
    elif ctx["embutidas"]:
        itens.append(
            f"🖼️ **{ctx['embutidas']} figuras embutidas** no próprio documento como "
            "`data:` URI — não há pasta de assets, e o arquivo é autocontido."
        )
    elif ctx["n_img"]:
        itens.append(
            f"⚠️ **{ctx['n_img']} figuras referenciadas, nenhuma recebida.** Verifique "
            "se a conversão usou `format=zip` — com `format=json` o serviço apaga os assets."
        )
    if ctx["paginas"]:
        itens.append(
            f"🔍 **Páginas para conferência** em "
            f"[`{ctx['paginas'].name}/`]({ctx['paginas'].name}/) — use estas, e não as "
            "figuras recortadas, para conferir números contra o original."
        )
    if ctx["strip_regex"]:
        itens.append(
            f"⚠️ **Ruído removido** por `--strip-regex`: `{ctx['strip_regex']}`. Se era "
            "carimbo de licença, registre aqui a procedência antes de compartilhar o arquivo."
        )
    if info["tem_texto"] is False:
        itens.append(
            "⚠️ **Sem camada de texto na origem** — o resultado passou por OCR e exige "
            "conferência contra a imagem da página."
        )
    return itens


def _inline_html(texto: str) -> str:
    """Converte o markdown inline usado nos itens de procedência (só o que emitimos)."""
    texto = re.sub(r"\[`?([^\]`]+)`?\]\(([^)]+)\)", r'<a href="\2">\1</a>', texto)
    texto = re.sub(r"\*\*([^*]+)\*\*", r"<strong>\1</strong>", texto)
    texto = re.sub(r"`([^`]+)`", r"<code>\1</code>", texto)
    return texto


def aplicar_cabecalho(texto: str, origem: Path, info: dict, ctx: dict, is_html: bool) -> str:
    """Prefixa a procedência no Markdown; injeta no `<body>` quando for HTML.

    Escrever blockquote de Markdown dentro de um `.html` não renderiza, e colocar
    qualquer coisa antes do `<!DOCTYPE html>` invalida o documento.
    """
    itens = itens_procedencia(origem, info, ctx)
    titulo = f"{origem.stem} — texto integral"

    if not is_html:
        linhas = [
            f"<!-- Caminho relativo: {'/'.join(Path(ctx['saida']).parts[-3:])} -->",
            f"# {titulo}",
            "",
        ]
        for i, item in enumerate(itens):
            if i:
                linhas.append(">")
            linhas += [f"> {linha}" for linha in item.split("\n")]
        return "\n".join(linhas + ["", "---", ""]) + texto

    bloco = (
        '<aside style="border-left:4px solid #888;padding:.5em 1em;margin:1em 0;'
        'font-family:system-ui,sans-serif;background:#f6f6f6;color:#222">\n'
        f"<h1>{titulo}</h1>\n"
        + "\n".join(f"<p>{_inline_html(i)}</p>" for i in itens)
        + "\n</aside>\n"
    )
    m = re.search(r"<body[^>]*>", texto, flags=re.I)
    if m:
        return texto[: m.end()] + "\n" + bloco + texto[m.end():]
    return bloco + texto


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("pdf", type=Path)
    ap.add_argument("--out", type=Path, required=True, help="destino .md (ou .html com --html)")
    ap.add_argument("--url", default="http://localhost:8010")
    ap.add_argument("--timeout", type=int, default=3600)
    ap.add_argument("--paginas", default="", help="páginas a extrair como PNG, ex.: 12,22,31")
    ap.add_argument("--dpi", type=int, default=150)
    ap.add_argument("--strip-regex", default=None,
                    help="linhas a remover do texto (carimbo de licença, rodapé repetido)")
    ap.add_argument("--sem-figuras", action="store_true",
                    help="desliga a descrição de figuras por VLM (corta o tempo pela metade)")
    ap.add_argument("--modelo-figuras", default="smolvlm-500m",
                    choices=["smolvlm", "smolvlm-500m", "granite", "granite-api"],
                    help=("VLM que descreve as figuras. Default 'smolvlm-500m': lê rótulos "
                          "de diagramas, ao contrário do 'smolvlm' (256M) do serviço, e "
                          "cabe em 8 GB — onde 'granite' in-process não cabe. 'granite-api' "
                          "dá a melhor leitura, mas exige servidor local com o modelo."))
    ap.add_argument("--sem-formulas", action="store_true",
                    help="desliga o LaTeX semântico das equações (raramente desejável)")
    ap.add_argument("--html", action="store_true",
                    help="saída HTML nativa: tabelas como <table> reais, com células mescladas")
    ap.add_argument("--remove-blocos", action="store_true",
                    help="remove blocos repetidos por contagem no servidor (sem LLM)")
    args = ap.parse_args()

    if not args.pdf.exists():
        erro(f"{args.pdf} não existe")

    import requests
    try:
        saude = requests.get(f"{args.url.rstrip('/')}/health", timeout=10).json()
    except Exception as exc:
        erro(f"serviço docling inacessível em {args.url} ({exc}). Suba-o antes.")
    print(f"docling: {saude}")

    info = triagem(args.pdf)
    print(f"entrada: {info['paginas']} páginas, cifrado={info['cifrado']}, "
          f"camada de texto={info['tem_texto']}")
    if info["tem_texto"] is False:
        print("aviso: sem camada de texto — o docling fará OCR e o resultado exige conferência",
              file=sys.stderr)

    ext = "html" if args.html else "md"
    params = {
        "output_format": "html" if args.html else "markdown",
        "formula_enrichment": str(not args.sem_formulas).lower(),
        "picture_description": str(not args.sem_figuras).lower(),
        "picture_description_model": args.modelo_figuras,
        "remove_blocks": str(args.remove_blocos).lower(),
        # enhance fica sempre desligado: medido no golden do serviço, o pós-processamento
        # por LLM não melhora o placar e corrompe conteúdo factual (reescreveu "Mercúrio"
        # como "Mercuryo"). Alteração silenciosa e plausível é inaceitável numa extração
        # destinada a ser citada.
        "enhance": "false",
        # Só age com enhance=true + vision_provider. O serviço atualizado já usa
        # `false` como default; mantido explícito para o caso de a skill rodar
        # contra uma instância antiga, onde o default `true` prometia uma limpeza
        # que não acontecia.
        "remove_headers_footers": "false",
    }
    # `remove_headers_footers` fica fora do cabeçalho por ser sempre false e não
    # descrever o resultado; o modelo do VLM entra porque muda o que a descrição diz.
    flags = ", ".join(
        f"{k}={v}" for k, v in params.items() if k != "remove_headers_footers"
    )

    with tempfile.TemporaryDirectory() as tmp:
        envio = args.pdf
        if info["cifrado"]:
            envio = decifrar(args.pdf, Path(tmp) / "sem-cifra.pdf")
            print("decifrado com pikepdf (PDF cifrado faz o docling devolver HTTP 500)")

        # 0,5 s/página sem figuras; ~1,1 s/página com descrição de figuras.
        por_pagina = 0.55 if args.sem_figuras else 1.15
        print(f"convertendo… ~{max(30, int(info['paginas'] * por_pagina))}s estimados "
              f"para {info['paginas']} páginas")
        blob, segundos = converter(envio, args.url, args.timeout, params)

    args.out.parent.mkdir(parents=True, exist_ok=True)
    texto, dir_assets = desempacotar(blob, args.out, ext)
    n_assets = len(list(dir_assets.iterdir())) if dir_assets else 0
    n_img = texto.count("![Image](") + texto.count("<img ")

    if args.strip_regex:
        antes = len(texto.splitlines())
        texto = re.sub(rf"^.*{args.strip_regex}.*$\n?", "", texto, flags=re.M)
        print(f"ruído removido: {antes - len(texto.splitlines())} linhas")

    dir_paginas = None
    if args.paginas:
        dir_paginas = args.out.with_name(f"{args.out.stem}_paginas")
        pags = [int(p) for p in args.paginas.split(",") if p.strip()]
        geradas = extrair_paginas(args.pdf, pags, dir_paginas, args.dpi)
        print(f"páginas extraídas: {len(geradas)} em {dir_paginas}")

    ctx = {
        "saida": str(args.out), "segundos": segundos, "flags": flags,
        "formulas": not args.sem_formulas, "assets": dir_assets, "n_assets": n_assets,
        "n_img": n_img, "embutidas": texto.count("data:image"),
        "paginas": dir_paginas, "strip_regex": args.strip_regex,
    }
    args.out.write_text(
        aplicar_cabecalho(texto, args.pdf, info, ctx, args.html), encoding="utf-8"
    )

    print(f"\ngravado: {args.out}")
    print(f"  {len(texto.split()):,} palavras · {texto.count('|---') or texto.count('<table')} tabelas · "
          f"{n_assets} figuras extraídas · {segundos:.0f}s")
    if dir_assets:
        print(f"  assets: {dir_assets}")
    print("\nPróximo passo: escreva ao lado um arquivo de transcrição conferida com as")
    print("equações e tabelas que importam. A extração integral é fonte, não resposta.")


if __name__ == "__main__":
    main()
