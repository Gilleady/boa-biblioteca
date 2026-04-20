from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

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

router = APIRouter(prefix="/usuarios", tags=["usuarios"])


def get_usuario_service(
    session: AsyncSession = Depends(get_async_session),
) -> UsuarioService:
    return UsuarioService(
        usuario_repository=UsuarioRepository(session),
        pessoa_repository=PessoaRepository(session),
    )


@router.get("", response_model=UsuarioListResponse)
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


@router.get("/{usuario_id}", response_model=UsuarioRead)
async def get_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    return await service.get(usuario_id)


@router.post("", response_model=UsuarioRead, status_code=status.HTTP_201_CREATED)
async def create_usuario(
    payload: UsuarioCreate,
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    return await service.create(payload)


@router.patch("/{usuario_id}", response_model=UsuarioRead)
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


@router.delete("/{usuario_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_usuario(
    usuario_id: UUID,
    service: UsuarioService = Depends(get_usuario_service),
) -> Response:
    await service.delete(usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
