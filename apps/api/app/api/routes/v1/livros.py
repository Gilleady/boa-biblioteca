from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.db.session import get_async_session
from app.repositories.livro import LivroRepository
from app.schemas.livro import LivroCreate, LivroListResponse, LivroRead, LivroUpdate
from app.services.livro import LivroService

router = APIRouter(prefix="/livros", tags=["livros"])


def get_livro_service(
    session: AsyncSession = Depends(get_async_session),
) -> LivroService:
    return LivroService(LivroRepository(session))


@router.get("", response_model=LivroListResponse)
async def list_livros(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    titulo: str | None = Query(default=None, min_length=1, max_length=255),
    disponivel: bool | None = None,
    service: LivroService = Depends(get_livro_service),
) -> LivroListResponse:
    return await service.list(
        page=page,
        page_size=page_size,
        titulo=titulo,
        disponivel=disponivel,
    )


@router.get("/{livro_id}", response_model=LivroRead)
async def get_livro(
    livro_id: UUID,
    service: LivroService = Depends(get_livro_service),
) -> LivroRead:
    return await service.get(livro_id)


@router.post("", response_model=LivroRead, status_code=status.HTTP_201_CREATED)
async def create_livro(
    payload: LivroCreate,
    service: LivroService = Depends(get_livro_service),
) -> LivroRead:
    return await service.create(payload)


@router.patch("/{livro_id}", response_model=LivroRead)
async def update_livro(
    livro_id: UUID,
    payload: LivroUpdate,
    service: LivroService = Depends(get_livro_service),
) -> LivroRead:
    if not payload.model_dump(exclude_unset=True):
        raise AppError(
            status_code=400,
            code="invalid_payload",
            message="Payload de atualizacao vazio",
        )

    return await service.update(livro_id, payload)


@router.delete("/{livro_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_livro(
    livro_id: UUID,
    service: LivroService = Depends(get_livro_service),
) -> Response:
    await service.delete(livro_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
