from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Response, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_admin_or_atendente
from app.api.docs import (
    AUTH_401_RESPONSE,
    CONFLICT_409_RESPONSE,
    FORBIDDEN_403_RESPONSE,
    INVALID_PAYLOAD_400_RESPONSE,
    NOT_FOUND_404_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.exceptions import AppError
from app.core.roles import ROLE_ATENDENTE, ROLE_LEITOR
from app.db.session import get_async_session
from app.models.usuario import Usuario
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


@router.get(
    "",
    response_model=UsuarioListResponse,
    summary="List users",
    description="Returns paginated users with optional username/ativo filters.",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def list_usuarios(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    username: str | None = Query(default=None, min_length=1, max_length=80),
    ativo: bool | None = None,
    _: Usuario = Security(get_admin_or_atendente),
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
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
    },
)
async def get_usuario(
    usuario_id: UUID,
    _: Usuario = Security(get_admin_or_atendente),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    return await service.get(usuario_id)


@router.post(
    "",
    response_model=UsuarioRead,
    status_code=status.HTTP_201_CREATED,
    summary="Create user",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        409: CONFLICT_409_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def create_usuario(
    payload: UsuarioCreate,
    actor: Usuario = Security(get_admin_or_atendente),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    if actor.papel == ROLE_ATENDENTE:
        payload = payload.model_copy(update={"papel": ROLE_LEITOR})

    return await service.create(payload, actor_id=actor.id)


@router.patch(
    "/{usuario_id}",
    response_model=UsuarioRead,
    summary="Update user",
    responses={
        400: INVALID_PAYLOAD_400_RESPONSE,
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
        409: CONFLICT_409_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def update_usuario(
    usuario_id: UUID,
    payload: UsuarioUpdate,
    actor: Usuario = Security(get_admin_or_atendente),
    service: UsuarioService = Depends(get_usuario_service),
) -> UsuarioRead:
    if not payload.model_dump(exclude_unset=True):
        raise AppError(
            status_code=400,
            code="invalid_payload",
            message="Payload de atualizacao vazio",
        )

    if actor.papel == ROLE_ATENDENTE and (
        payload.papel is not None or payload.pessoa_id is not None
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions",
        )

    return await service.update(usuario_id, payload, actor_id=actor.id)


@router.delete(
    "/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete user",
    responses={
        401: AUTH_401_RESPONSE,
        403: FORBIDDEN_403_RESPONSE,
        404: NOT_FOUND_404_RESPONSE,
    },
)
async def delete_usuario(
    usuario_id: UUID,
    _: Usuario = Security(get_admin_or_atendente),
    service: UsuarioService = Depends(get_usuario_service),
) -> Response:
    await service.delete(usuario_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
