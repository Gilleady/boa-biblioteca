from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import (
    get_admin_or_atendente,
    get_current_usuario,
    resolve_emprestimo_scope_pessoa_id,
)
from app.api.docs import (
    AUTH_401_RESPONSE,
    FORBIDDEN_403_RESPONSE,
    NOT_FOUND_404_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.roles import ROLE_LEITOR
from app.db.session import get_async_session
from app.models.usuario import Usuario
from app.repositories.emprestimo import EmprestimoRepository
from app.repositories.livro import LivroRepository
from app.repositories.pessoa import PessoaRepository
from app.schemas.emprestimo import (
    EmprestimoCreate,
    EmprestimoListResponse,
    EmprestimoRead,
)
from app.services.emprestimo import EmprestimoService

router = APIRouter(prefix="/emprestimos", tags=["emprestimos"])


def get_emprestimo_service(
    session: AsyncSession = Depends(get_async_session),
) -> EmprestimoService:
    return EmprestimoService(
        EmprestimoRepository(session),
        LivroRepository(session),
        PessoaRepository(session),
    )


@router.get(
    "",
    response_model=EmprestimoListResponse,
    summary="List loans",
    description="Returns paginated loans with optional filters.",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def list_emprestimos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    pessoa_id: UUID | None = Query(default=None),
    ativo: bool | None = None,
    order_by: Literal["created_at", "data_emprestimo"] = "created_at",
    order_direction: Literal["asc", "desc"] = "desc",
    usuario: Usuario = Security(get_current_usuario),
    service: EmprestimoService = Depends(get_emprestimo_service),
) -> EmprestimoListResponse:
    scoped_pessoa_id = resolve_emprestimo_scope_pessoa_id(
        usuario=usuario,
        requested_pessoa_id=pessoa_id,
    )

    return await service.list(
        page=page,
        page_size=page_size,
        pessoa_id=scoped_pessoa_id,
        ativo=ativo,
        order_by=order_by,
        order_direction=order_direction,
    )


@router.get(
    "/{emprestimo_id}",
    response_model=EmprestimoRead,
    summary="Get loan by id",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
    },
)
async def get_emprestimo(
    emprestimo_id: UUID,
    usuario: Usuario = Security(get_current_usuario),
    service: EmprestimoService = Depends(get_emprestimo_service),
) -> EmprestimoRead:
    emprestimo = await service.get(emprestimo_id)

    if usuario.papel == ROLE_LEITOR and emprestimo.pessoa_id != usuario.pessoa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Leitor can only access own loans",
        )

    return emprestimo


@router.post(
    "",
    response_model=EmprestimoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new loan",
    description="Create a loan for a person to borrow a book.",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
        409: {
            "description": "Conflict - book unavailable or person has active loan",
            "content": {
                "application/json": {"example": {"code": "livro_indisponivel"}}
            },
        },
        422: VALIDATION_422_RESPONSE,
    },
)
async def create_emprestimo(
    payload: EmprestimoCreate,
    service: EmprestimoService = Depends(get_emprestimo_service),
    actor: Usuario = Security(get_admin_or_atendente),
) -> EmprestimoRead:
    return await service.create(payload, actor_id=actor.id)


@router.patch(
    "/{emprestimo_id}/devolver",
    response_model=EmprestimoRead,
    summary="Return a book",
    description="Mark a loan as returned and make the book available again.",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
        409: {
            "description": "Conflict - loan is not active",
            "content": {
                "application/json": {"example": {"code": "emprestimo_nao_ativo"}}
            },
        },
    },
)
async def devolucao_emprestimo(
    emprestimo_id: UUID,
    service: EmprestimoService = Depends(get_emprestimo_service),
    actor: Usuario = Security(get_admin_or_atendente),
) -> EmprestimoRead:
    return await service.devolucao(emprestimo_id, actor_id=actor.id)
