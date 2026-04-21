from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_usuario
from app.api.docs import (
    AUTH_401_RESPONSE,
    NOT_FOUND_404_RESPONSE,
    VALIDATION_422_RESPONSE,
)
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
    responses={422: VALIDATION_422_RESPONSE},
)
async def list_emprestimos(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    pessoa_id: UUID | None = Query(default=None),
    ativo: bool | None = None,
    order_by: Literal["created_at", "data_emprestimo"] = "created_at",
    order_direction: Literal["asc", "desc"] = "desc",
    service: EmprestimoService = Depends(get_emprestimo_service),
) -> EmprestimoListResponse:
    return await service.list(
        page=page,
        page_size=page_size,
        pessoa_id=pessoa_id,
        ativo=ativo,
        order_by=order_by,
        order_direction=order_direction,
    )


@router.get(
    "/{emprestimo_id}",
    response_model=EmprestimoRead,
    summary="Get loan by id",
    responses={404: NOT_FOUND_404_RESPONSE},
)
async def get_emprestimo(
    emprestimo_id: UUID,
    service: EmprestimoService = Depends(get_emprestimo_service),
) -> EmprestimoRead:
    return await service.get(emprestimo_id)


@router.post(
    "",
    response_model=EmprestimoRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new loan",
    description="Create a loan for a person to borrow a book.",
    responses={
        401: AUTH_401_RESPONSE,
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
    _: Usuario = Security(get_current_usuario),
) -> EmprestimoRead:
    return await service.create(payload)


@router.patch(
    "/{emprestimo_id}/devolver",
    response_model=EmprestimoRead,
    summary="Return a book",
    description="Mark a loan as returned and make the book available again.",
    responses={
        401: AUTH_401_RESPONSE,
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
    _: Usuario = Security(get_current_usuario),
) -> EmprestimoRead:
    return await service.devolucao(emprestimo_id)
