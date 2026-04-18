from __future__ import annotations

from uuid import UUID

from app.core.exceptions import AppError
from app.repositories.livro import LivroRepository
from app.schemas.livro import LivroCreate, LivroListResponse, LivroRead, LivroUpdate


class LivroService:
    def __init__(self, repository: LivroRepository) -> None:
        self._repository = repository

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        titulo: str | None,
        disponivel: bool | None,
    ) -> LivroListResponse:
        livros, total = await self._repository.list(
            page=page,
            page_size=page_size,
            titulo=titulo,
            disponivel=disponivel,
        )

        return LivroListResponse(
            items=[LivroRead.model_validate(livro) for livro in livros],
            total=total,
            page=page,
            page_size=page_size,
        )

    async def get(self, livro_id: UUID) -> LivroRead:
        livro = await self._repository.get_by_id(livro_id)
        if livro is None:
            raise AppError(
                status_code=404,
                code="livro_not_found",
                message="Livro nao encontrado",
                details={"id": str(livro_id)},
            )

        return LivroRead.model_validate(livro)

    async def create(self, payload: LivroCreate) -> LivroRead:
        livro = await self._repository.create(payload)
        return LivroRead.model_validate(livro)

    async def update(self, livro_id: UUID, payload: LivroUpdate) -> LivroRead:
        livro = await self._repository.get_by_id(livro_id)
        if livro is None:
            raise AppError(
                status_code=404,
                code="livro_not_found",
                message="Livro nao encontrado",
                details={"id": str(livro_id)},
            )

        updated = await self._repository.update(livro, payload)
        return LivroRead.model_validate(updated)

    async def delete(self, livro_id: UUID) -> None:
        livro = await self._repository.get_by_id(livro_id)
        if livro is None:
            raise AppError(
                status_code=404,
                code="livro_not_found",
                message="Livro nao encontrado",
                details={"id": str(livro_id)},
            )

        await self._repository.delete(livro)
