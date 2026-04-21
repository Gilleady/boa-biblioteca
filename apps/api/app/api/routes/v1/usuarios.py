from __future__ import annotations

from uuid import UUID

from app.api.docs import (
    CONFLICT_409_RESPONSE,
    INVALID_PAYLOAD_400_RESPONSE,
    NOT_FOUND_404_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.exceptions import AppError
from app.db.session import get_async_session
from app.repositories.pessoa import PessoaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioRead,
    UsuarioUpdate,
)
from app.services.usuario import UsuarioService
from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def get_usuario_service(
    session: AsyncSession = Depends(get_async_session),
) -> UsuarioService:
    return UsuarioService(
        usuario_repository=UsuarioRepository(session),
        pessoa_repository=PessoaRepository(session),
    )


@router.get(
    "",
    response_model=UsuarioListResponse,
    summary="List users",
    description="Returns paginated users with optional username/ativo filters.",
    responses={422: VALIDATION_422_RESPONSE},
)
async def list_usuarios(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    username: str | None = Query(default=None, min_length=1, max_length=80),
    ativo: bool | None = None,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioListResponse:
    return await service.list(
        page=page,
        page_size=page_size,
        username=username,
        ativo=ativo,
    )


@router.get(
    "/{usuario_id}",
    response_model=UsuarioRead,
    summary="Get user by id",
    responses={404: NOT_FOUND_404_RESPONSE},
)
async def get_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    return await service.get(usuario_id)


@router.post(
    "",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    responses={409: CONFLICT_409_RESPONSE, 422: VALIDATION_422_RESPONSE},
)
async def create_usuario(
    payload: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    return await service.create(payload)


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioRead,
    summary="Update user",
    responses={
        400: INVALID_PAYLOAD_400_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
        409: CONFLICT_409_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def update_usuario(
    usuario_id: UUID,
    payload: UsuarioUpdate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    if not payload.model_dump(exclude_unset=True):
        raise AppError(
            status_code=400,
            code="invalid_payload",
            message="Payload de atualizacao vazio",
        )

    return await service.update(usuario_id, payload)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    responses={404: NOT_FOUND_404_RESPONSE},
)
async def delete_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> Response:
    await service.delete(usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
