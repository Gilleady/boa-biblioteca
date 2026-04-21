from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.docs import (
    CONFLICT_409_RESPONSE,
    INVALID_PAYLOAD_400_RESPONSE,
    NOT_FOUND_404_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.exceptions import AppError
from app.db.session import get_async_session
from app.repositories.pessoa import PessoaRepository
from app.schemas.pessoa import (
    PessoaCreate,
    PessoaListResponse,
    PessoaRead,
    PessoaUpdate,
)
from app.services.pessoa import PessoaService

router = APIRouter(prefix="/pessoas", tags=["pessoas"])


def get_pessoa_service(
    session: AsyncSession = Depends(get_async_session),
) -> PessoaService:
    return PessoaService(PessoaRepository(session))


@router.get(
    "",
    response_model=PessoaListResponse,
    summary="List people",
    description="Returns paginated people with optional nome/email filters.",
    responses={422: VALIDATION_422_RESPONSE},
)
async def list_pessoas(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    nome: str | None = Query(default=None, min_length=1, max_length=255),
    email: str | None = Query(default=None, min_length=3, max_length=255),
    service: PessoaService = Depends(get_pessoa_service),
) -> PessoaListResponse:
    return await service.list(
        page=page,
        page_size=page_size,
        nome=nome,
        email=email,
    )


@router.get(
    "/{pessoa_id}",
    response_model=PessoaRead,
    summary="Get person by id",
    responses={404: NOT_FOUND_404_RESPONSE},
)
async def get_pessoa(
    pessoa_id: UUID,
    service: PessoaService = Depends(get_pessoa_service),
) -> PessoaRead:
    return await service.get(pessoa_id)


@router.post(
    "",
    response_model=PessoaRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create person",
    responses={409: CONFLICT_409_RESPONSE, 422: VALIDATION_422_RESPONSE},
)
async def create_pessoa(
    payload: PessoaCreate,
    service: PessoaService = Depends(get_pessoa_service),
) -> PessoaRead:
    return await service.create(payload)


@router.patch(
    "/{pessoa_id}",
    response_model=PessoaRead,
    summary="Update person",
    responses={
        400: INVALID_PAYLOAD_400_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
        409: CONFLICT_409_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def update_pessoa(
    pessoa_id: UUID,
    payload: PessoaUpdate,
    service: PessoaService = Depends(get_pessoa_service),
) -> PessoaRead:
    if not payload.model_dump(exclude_unset=True):
        raise AppError(
            status_code=400,
            code="invalid_payload",
            message="Payload de atualizacao vazio",
        )

    return await service.update(pessoa_id, payload)


@router.delete(
    "/{pessoa_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete person",
    responses={404: NOT_FOUND_404_RESPONSE},
)
async def delete_pessoa(
    pessoa_id: UUID,
    service: PessoaService = Depends(get_pessoa_service),
) -> Response:
    await service.delete(pessoa_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
