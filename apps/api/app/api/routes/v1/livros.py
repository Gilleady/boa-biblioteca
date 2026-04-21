from __future__ import annotations

from typing import Literal
from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_usuario
from app.api.docs import (
    AUTH_401_RESPONSE,
    INVALID_PAYLOAD_400_RESPONSE,
    NOT_FOUND_404_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.exceptions import AppError
from app.db.session import get_async_session
from app.models.usuario import Usuario
from app.repositories.livro import LivroRepository
from app.schemas.livro import LivroCreate, LivroListResponse, LivroRead, LivroUpdate
from app.services.livro import LivroService

router = APIRouter(prefix="/livros", tags=["livros"])


def get_livro_service(
    session: AsyncSession = Depends(get_async_session),
) -> LivroService:
    return LivroService(LivroRepository(session))


@router.get(
    "",
    response_model=LivroListResponse,
    summary="List books",
    description="Returns paginated books with optional filters and sorting.",
    responses={422: VALIDATION_422_RESPONSE},
)
async def list_livros(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    titulo: str | None = Query(default=None, min_length=1, max_length=255),
    autor: str | None = Query(default=None, min_length=1, max_length=255),
    ano_publicacao: int | None = Query(default=None, ge=0, le=2100),
    disponivel: bool | None = None,
    order_by: Literal["created_at", "titulo", "ano_publicacao"] = "created_at",
    order_direction: Literal["asc", "desc"] = "desc",
    service: LivroService = Depends(get_livro_service),
) -> LivroListResponse:
    return await service.list(
        page=page,
        page_size=page_size,
        titulo=titulo,
        autor=autor,
        ano_publicacao=ano_publicacao,
        disponivel=disponivel,
        order_by=order_by,
        order_direction=order_direction,
    )


@router.get(
    "/{livro_id}",
    response_model=LivroRead,
    summary="Get book by id",
    responses={404: NOT_FOUND_404_RESPONSE},
)
async def get_livro(
    livro_id: UUID,
    service: LivroService = Depends(get_livro_service),
) -> LivroRead:
    return await service.get(livro_id)


@router.post(
    "",
    response_model=LivroRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new book",
    responses={401: AUTH_401_RESPONSE, 422: VALIDATION_422_RESPONSE},
)
async def create_livro(
    payload: LivroCreate,
    service: LivroService = Depends(get_livro_service),
    _: Usuario = Security(get_current_usuario),
) -> LivroRead:
    return await service.create(payload)


@router.patch(
    "/{livro_id}",
    response_model=LivroRead,
    summary="Update a book",
    responses={
        400: INVALID_PAYLOAD_400_RESPONSE,
        401: AUTH_401_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def update_livro(
    livro_id: UUID,
    payload: LivroUpdate,
    service: LivroService = Depends(get_livro_service),
    _: Usuario = Security(get_current_usuario),
) -> LivroRead:
    if not payload.model_dump(exclude_unset=True):
        raise AppError(
            status_code=400,
            code="invalid_payload",
            message="Payload de atualizacao vazio",
        )

    return await service.update(livro_id, payload)


@router.delete(
    "/{livro_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a book",
    responses={401: AUTH_401_RESPONSE, 404: NOT_FOUND_404_RESPONSE},
)
async def delete_livro(
    livro_id: UUID,
    service: LivroService = Depends(get_livro_service),
    _: Usuario = Security(get_current_usuario),
) -> Response:
    await service.delete(livro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
