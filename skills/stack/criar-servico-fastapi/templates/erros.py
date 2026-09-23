# Caminho relativo: src/<pacote>/erros.py
# Modelo da skill criar-servico-fastapi: erro do domínio é do domínio; HTTP é da borda.
#
# O domínio levanta ErroDominio; o handler traduz para status e corpo. Assim a mesma regra
# serve a outro transporte (fila, CLI), e o cliente nunca recebe Traceback nem SQL.
import logging

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

log = logging.getLogger(__name__)


class ErroDominio(Exception):
    """Base. Cada subclasse carrega o status que a borda deve usar."""
    status = 400
    codigo = "erro_dominio"

    def __init__(self, mensagem: str):
        super().__init__(mensagem)
        self.mensagem = mensagem


class NaoEncontrado(ErroDominio):
    status, codigo = 404, "nao_encontrado"


class Conflito(ErroDominio):
    """Ex.: reserva sobreposta — 409, não 400."""
    status, codigo = 409, "conflito"


class SemPermissao(ErroDominio):
    status, codigo = 403, "sem_permissao"


def registrar(app: FastAPI) -> None:
    @app.exception_handler(ErroDominio)
    async def _dominio(_: Request, exc: ErroDominio) -> JSONResponse:
        return JSONResponse(status_code=exc.status,
                            content={"codigo": exc.codigo, "mensagem": exc.mensagem})

    @app.exception_handler(Exception)
    async def _inesperado(req: Request, exc: Exception) -> JSONResponse:
        # Detalhe completo no log; ao cliente, só o que ele pode fazer com isso.
        log.exception("falha inesperada em %s %s", req.method, req.url.path)
        return JSONResponse(status_code=500,
                            content={"codigo": "erro_interno", "mensagem": "falha interna"})
