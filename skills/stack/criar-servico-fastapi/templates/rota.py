# Caminho relativo: src/<pacote>/rotas/<recurso>.py
# Modelo da skill criar-servico-fastapi: a rota é a borda. Valida, delega, traduz.
from fastapi import APIRouter, Depends, Query, status

from ..deps import sessao, usuario_atual
from ..dominio import reservas            # o domínio NÃO importa fastapi
from ..esquemas.reserva import ReservaCria, ReservaLe, Pagina

rotas = APIRouter(prefix="/reservas", tags=["reservas"])


@rotas.post("", response_model=ReservaLe, status_code=status.HTTP_201_CREATED)
async def criar(corpo: ReservaCria, sess=Depends(sessao), usuario=Depends(usuario_atual)):
    # Pydantic já validou formato e tipo; o domínio valida a REGRA (sobreposição, limite).
    reserva = await reservas.criar(sess, dono=usuario.id, **corpo.model_dump())
    return reserva          # response_model poda o que não deve sair


@rotas.get("", response_model=Pagina[ReservaLe])
async def listar(
    sess=Depends(sessao),
    usuario=Depends(usuario_atual),
    # Lista SEMPRE paginada: limite padrão e máximo, ambos declarados.
    pagina: int = Query(1, ge=1),
    tamanho: int = Query(50, ge=1, le=200),
):
    itens, total = await reservas.listar(sess, dono=usuario.id, pagina=pagina, tamanho=tamanho)
    return Pagina[ReservaLe](itens=itens, total=total, pagina=pagina, tamanho=tamanho)
