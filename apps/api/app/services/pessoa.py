from __future__ import annotations

from uuid import UUID

from app.core.exceptions import AppError
from app.repositories.pessoa import PessoaRepository
from app.schemas.pessoa import (
    PessoaCreate,
    PessoaListResponse,
    PessoaRead,
    PessoaUpdate,
)


class PessoaService:
    def __init__(self, repository: PessoaRepository) -> None:
        self._repository = repository

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        nome: str | None,
        email: str | None,
    ) -> PessoaListResponse:
        pessoas, total = await self._repository.list(
            page=page,
            page_size=page_size,
            nome=nome,
            email=email,
        )

        return PessoaListResponse(
            items=[PessoaRead.model_validate(pessoa) for pessoa in pessoas],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get(self, pessoa_id: UUID) -> PessoaRead:
        pessoa = await self._repository.get_by_id(pessoa_id)
        if pessoa is None:
            raise AppError(
                status_code=404,
                code="pessoa_not_found",
                message="Pessoa nao encontrada",
                details={"id": str(pessoa_id)},
            )

        return PessoaRead.model_validate(pessoa)

    async def create(
        self,
        payload: PessoaCreate,
        actor_id: UUID | None = None,
    ) -> PessoaRead:
        pessoa = await self._repository.create(payload, actor_id=actor_id)
        return PessoaRead.model_validate(pessoa)

    async def update(
        self,
        pessoa_id: UUID,
        payload: PessoaUpdate,
        actor_id: UUID | None = None,
    ) -> PessoaRead:
        pessoa = await self._repository.get_by_id(pessoa_id)
        if pessoa is None:
            raise AppError(
                status_code=404,
                code="pessoa_not_found",
                message="Pessoa nao encontrada",
                details={"id": str(pessoa_id)},
            )

        updated = await self._repository.update(
            pessoa,
            payload,
            actor_id=actor_id,
        )
        return PessoaRead.model_validate(updated)

    async def delete(self, pessoa_id: UUID) -> None:
        pessoa = await self._repository.get_by_id(pessoa_id)
        if pessoa is None:
            raise AppError(
                status_code=404,
                code="pessoa_not_found",
                message="Pessoa nao encontrada",
                details={"id": str(pessoa_id)},
            )

        await self._repository.delete(pessoa)
