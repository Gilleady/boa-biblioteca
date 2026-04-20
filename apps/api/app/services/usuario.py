from __future__ import annotations

from uuid import UUID

from app.core.exceptions import AppError
from app.repositories.pessoa import PessoaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.usuario import (
    UsuarioCreate,
    UsuarioListResponse,
    UsuarioRead,
    UsuarioUpdate,
)


class UsuarioService:
    def __init__(
        self,
        usuario_repository: UsuarioRepository,
        pessoa_repository: PessoaRepository,
    ) -> None:
        self._usuario_repository = usuario_repository
        self._pessoa_repository = pessoa_repository

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        username: str | None,
        ativo: bool | None,
    ) -> UsuarioListResponse:
        usuarios, total = await self._usuario_repository.list(
            page=page,
            page_size=page_size,
            username=username,
            ativo=ativo,
        )

        return UsuarioListResponse(
            items=[UsuarioRead.model_validate(usuario) for usuario in usuarios],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get(self, usuario_id: UUID) -> UsuarioRead:
        usuario = await self._usuario_repository.get_by_id(usuario_id)
        if usuario is None:
            raise AppError(
                status_code=404,
                code="usuario_not_found",
                message="Usuario nao encontrado",
                details={"id": str(usuario_id)},
            )

        return UsuarioRead.model_validate(usuario)

    async def create(self, payload: UsuarioCreate) -> UsuarioRead:
        await self._ensure_pessoa_exists(payload.pessoa_id)
        usuario = await self._usuario_repository.create(payload)
        return UsuarioRead.model_validate(usuario)

    async def update(self, usuario_id: UUID, payload: UsuarioUpdate) -> UsuarioRead:
        usuario = await self._usuario_repository.get_by_id(usuario_id)
        if usuario is None:
            raise AppError(
                status_code=404,
                code="usuario_not_found",
                message="Usuario nao encontrado",
                details={"id": str(usuario_id)},
            )

        if payload.pessoa_id is not None:
            await self._ensure_pessoa_exists(payload.pessoa_id)

        updated = await self._usuario_repository.update(usuario, payload)
        return UsuarioRead.model_validate(updated)

    async def delete(self, usuario_id: UUID) -> None:
        usuario = await self._usuario_repository.get_by_id(usuario_id)
        if usuario is None:
            raise AppError(
                status_code=404,
                code="usuario_not_found",
                message="Usuario nao encontrado",
                details={"id": str(usuario_id)},
            )

        await self._usuario_repository.delete(usuario)

    async def _ensure_pessoa_exists(self, pessoa_id: UUID) -> None:
        if await self._pessoa_repository.exists_by_id(pessoa_id):
            return

        raise AppError(
            status_code=404,
            code="pessoa_not_found",
            message="Pessoa nao encontrada",
            details={"id": str(pessoa_id)},
        )
