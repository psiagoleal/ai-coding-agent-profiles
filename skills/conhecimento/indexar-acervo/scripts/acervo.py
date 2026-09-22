#!/usr/bin/env python3
# Caminho relativo: skills/conhecimento/indexar-acervo/scripts/acervo.py
"""Base de conhecimento local sobre um acervo de arquivos: inventário, extração e índice FTS5.

    acervo.py inventariar <dir> [--raiz-nome N] [--db ARQ]
    acervo.py extrair [--limite N] [--ext .pdf,.md] [--db ARQ]
    acervo.py indexar [--recriar] [--db ARQ]
    acervo.py buscar "<consulta FTS5>" [--projeto P] [--categoria C] [--limite N]
    acervo.py estado [--db ARQ]

O acervo NÃO é movido nem copiado: o banco guarda texto extraído e proveniência, e todo
resultado aponta para o arquivo original. Todas as etapas são retomáveis.

Consulta FTS5: `flecha vento` (E), `"frase exata"`, `ampacid*`, `a OR b`, `NEAR(a b, 8)`.
"""
from __future__ import annotations

import argparse
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

DB_PADRAO = Path(".cache/acervo/acervo.db")
TEXTO = {".txt", ".md", ".rst", ".csv", ".tsv", ".json", ".yaml", ".yml", ".toml", ".ini",
         ".py", ".rs", ".c", ".h", ".cpp", ".hpp", ".sh", ".sql", ".tex", ".html", ".xml"}
IGNORAR_DIR = {".git", ".venv", "node_modules", "__pycache__", "target", ".cache"}
LIMITE_CHARS = 400_000  # texto por arquivo; acima disso, trunca e marca

DDL = """
CREATE TABLE IF NOT EXISTS arquivo (
    caminho   TEXT PRIMARY KEY,
    nome      TEXT NOT NULL,
    ext       TEXT,
    tamanho   INTEGER NOT NULL,
    mtime     TEXT NOT NULL,
    raiz      TEXT NOT NULL,
    projeto   TEXT,
    categoria TEXT
);
CREATE INDEX IF NOT EXISTS ix_arquivo_projeto ON arquivo(projeto);
CREATE TABLE IF NOT EXISTS documento (
    caminho     TEXT PRIMARY KEY,
    metodo      TEXT NOT NULL,          -- nativo | pdftotext | docx | xlsx | ...
    texto       TEXT,
    chars       INTEGER NOT NULL DEFAULT 0,
    truncado    INTEGER NOT NULL DEFAULT 0,
    erro        TEXT,                   -- falha de extração != arquivo inexistente
    extraido_em TEXT NOT NULL
);
CREATE VIRTUAL TABLE IF NOT EXISTS busca USING fts5(
    caminho UNINDEXED, nome, projeto UNINDEXED, categoria UNINDEXED, ext UNINDEXED, texto,
    tokenize = "unicode61 remove_diacritics 2"
);
CREATE TABLE IF NOT EXISTS indexado (caminho TEXT PRIMARY KEY);
"""


def agora() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def abrir(db: Path) -> sqlite3.Connection:
    db.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(db)
    con.executescript(DDL)
    return con


# ---------------------------------------------------------------- inventariar
def inventariar(con: sqlite3.Connection, base: Path, raiz_nome: str) -> int:
    novos = 0
    for dirpath, dirnames, filenames in os.walk(base):
        dirnames[:] = [d for d in dirnames if d not in IGNORAR_DIR and not d.startswith(".")]
        for nome in filenames:
            p = Path(dirpath) / nome
            try:
                st = p.stat()
            except OSError:
                continue  # link quebrado, permissão: não é arquivo do acervo
            rel = p.relative_to(base).parts
            con.execute(
                "INSERT OR REPLACE INTO arquivo VALUES (?,?,?,?,?,?,?,?)",
                (str(p), nome, p.suffix.lower(), st.st_size,
                 datetime.fromtimestamp(st.st_mtime, timezone.utc).isoformat(timespec="seconds"),
                 raiz_nome,
                 rel[0] if len(rel) > 1 else "",          # projeto = 1º nível
                 rel[1] if len(rel) > 2 else ""),         # categoria = 2º nível
            )
            novos += 1
    con.commit()
    return novos


# -------------------------------------------------------------------- extrair
def extrair_texto(p: Path) -> tuple[str, str, str | None]:
    """→ (metodo, texto, erro). Erro registrado é informação, não exceção."""
    ext = p.suffix.lower()
    try:
        if ext in TEXTO:
            return "nativo", p.read_text(encoding="utf-8", errors="replace"), None
        if ext == ".pdf":
            if not shutil.which("pdftotext"):
                return "pdftotext", "", "pdftotext ausente (instale poppler-utils)"
            r = subprocess.run(["pdftotext", "-q", "-enc", "UTF-8", str(p), "-"],
                               capture_output=True, text=True, timeout=300)
            if r.returncode != 0:
                return "pdftotext", "", (r.stderr.strip() or "falha")[:300]
            return "pdftotext", r.stdout, None
        if ext == ".docx":
            import docx  # opcional
            return "docx", "\n".join(par.text for par in docx.Document(str(p)).paragraphs), None
        if ext in (".xlsx", ".xlsm"):
            from openpyxl import load_workbook  # opcional
            wb = load_workbook(str(p), read_only=True, data_only=True)
            partes = []
            for aba in wb.worksheets:
                partes.append(f"# {aba.title}")
                for linha in aba.iter_rows(values_only=True):
                    partes.append("\t".join("" if c is None else str(c) for c in linha))
            return "xlsx", "\n".join(partes), None
    except ImportError as e:
        return ext.lstrip("."), "", f"biblioteca ausente: {e.name}"
    except Exception as e:  # arquivo corrompido, protegido, timeout
        return ext.lstrip("."), "", f"{type(e).__name__}: {e}"[:300]
    return "", "", "extensão sem extrator"


def extrair(con: sqlite3.Connection, limite: int, exts: set[str]) -> tuple[int, int]:
    q = ("SELECT caminho FROM arquivo WHERE caminho NOT IN (SELECT caminho FROM documento)")
    if exts:
        q += " AND ext IN (%s)" % ",".join("?" * len(exts))
    q += " LIMIT ?"
    alvos = [r[0] for r in con.execute(q, (*sorted(exts), limite) if exts else (limite,))]
    ok = falhou = 0
    for caminho in alvos:
        metodo, texto, erro = extrair_texto(Path(caminho))
        truncado = len(texto) > LIMITE_CHARS
        texto = texto[:LIMITE_CHARS]
        con.execute("INSERT OR REPLACE INTO documento VALUES (?,?,?,?,?,?,?)",
                    (caminho, metodo, texto or None, len(texto), int(truncado), erro, agora()))
        ok, falhou = (ok + 1, falhou) if erro is None else (ok, falhou + 1)
    con.commit()
    return ok, falhou


# -------------------------------------------------------------------- indexar
def indexar(con: sqlite3.Connection, recriar: bool) -> int:
    if recriar:
        con.executescript("DROP TABLE IF EXISTS busca; DELETE FROM indexado;")
        con.executescript(DDL)
    linhas = con.execute("""
        SELECT d.caminho, a.nome, a.projeto, a.categoria, a.ext, d.texto
        FROM documento d JOIN arquivo a ON a.caminho = d.caminho
        WHERE d.texto IS NOT NULL AND d.chars > 0
          AND d.caminho NOT IN (SELECT caminho FROM indexado)
    """).fetchall()
    for l in linhas:
        con.execute("INSERT INTO busca VALUES (?,?,?,?,?,?)", l)
        con.execute("INSERT OR IGNORE INTO indexado VALUES (?)", (l[0],))
    con.commit()
    return len(linhas)


# --------------------------------------------------------------------- buscar
def buscar(con: sqlite3.Connection, consulta: str, projeto: str, categoria: str,
           limite: int, chars: int) -> int:
    onde, param = ["busca MATCH ?"], [consulta]
    if projeto:
        onde.append("projeto = ?"); param.append(projeto)
    if categoria:
        onde.append("categoria = ?"); param.append(categoria)
    sql = (f"SELECT caminho, nome, projeto, categoria, "
           f"snippet(busca, 5, '[', ']', ' … ', 24) FROM busca "
           f"WHERE {' AND '.join(onde)} ORDER BY rank LIMIT ?")
    try:
        linhas = con.execute(sql, (*param, limite)).fetchall()
    except sqlite3.OperationalError as e:
        sys.exit(f"consulta FTS5 inválida: {e}")
    for caminho, nome, proj, cat, trecho in linhas:
        print(f"\n{caminho}\n  {nome} · projeto={proj or '-'} · categoria={cat or '-'}")
        print(f"  {' '.join(trecho.split())[:chars]}")
    return len(linhas)


def estado(con: sqlite3.Connection) -> None:
    n = lambda q: con.execute(q).fetchone()[0]
    print(json.dumps({
        "arquivos": n("SELECT count(*) FROM arquivo"),
        "extraidos": n("SELECT count(*) FROM documento WHERE erro IS NULL"),
        "com_erro": n("SELECT count(*) FROM documento WHERE erro IS NOT NULL"),
        "indexados": n("SELECT count(*) FROM indexado"),
        "por_metodo": dict(con.execute(
            "SELECT metodo, count(*) FROM documento GROUP BY metodo ORDER BY 2 DESC")),
    }, ensure_ascii=False, indent=1))


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--db", default=str(DB_PADRAO))
    sub = ap.add_subparsers(dest="cmd", required=True)
    i = sub.add_parser("inventariar"); i.add_argument("dir"); i.add_argument("--raiz-nome", default="")
    e = sub.add_parser("extrair"); e.add_argument("--limite", type=int, default=500); e.add_argument("--ext", default="")
    x = sub.add_parser("indexar"); x.add_argument("--recriar", action="store_true")
    b = sub.add_parser("buscar"); b.add_argument("consulta"); b.add_argument("--projeto", default="")
    b.add_argument("--categoria", default=""); b.add_argument("--limite", type=int, default=10)
    b.add_argument("--chars", type=int, default=300)
    sub.add_parser("estado")
    a = ap.parse_args()

    con = abrir(Path(a.db))
    if a.cmd == "inventariar":
        base = Path(a.dir).expanduser().resolve()
        if not base.is_dir():
            sys.exit(f"não é diretório: {base}")
        print(f"{inventariar(con, base, a.raiz_nome or base.name)} arquivos no inventário")
    elif a.cmd == "extrair":
        exts = {x if x.startswith(".") else f".{x}" for x in a.ext.split(",") if x}
        ok, falhou = extrair(con, a.limite, exts)
        print(f"extraídos: {ok} · com erro: {falhou} (erro fica registrado, ver 'estado')")
    elif a.cmd == "indexar":
        print(f"{indexar(con, a.recriar)} documentos indexados")
    elif a.cmd == "buscar":
        if buscar(con, a.consulta, a.projeto, a.categoria, a.limite, a.chars) == 0:
            print("nenhum resultado — verifique se a extração cobriu esse tipo de arquivo "
                  "('estado' mostra erros por método)", file=sys.stderr)
            return 1
    else:
        estado(con)
    return 0


if __name__ == "__main__":
    sys.exit(main())
