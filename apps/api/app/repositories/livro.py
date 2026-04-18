from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.livro import Livro
from app.schemas.livro import LivroCreate, LivroUpdate


class LivroRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        titulo: str | None,
        disponivel: bool | None,
    ) -> tuple[list[Livro], int]:
        stmt: Select[tuple[Livro]] = select(Livro)

        if titulo:
            stmt = stmt.where(Livro.titulo.ilike(f"%{titulo}%"))

        if disponivel is not None:
            stmt = stmt.where(Livro.disponivel.is_(disponivel))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        stmt = stmt.order_by(Livro.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, livro_id: UUID) -> Livro | None:
        result = await self._session.execute(select(Livro).where(Livro.id == livro_id))
        return result.scalar_one_or_none()

    async def create(self, payload: LivroCreate) -> Livro:
        livro = Livro(**payload.model_dump())
        self._session.add(livro)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                status_code=409,
                code="livro_conflict",
                message="Livro com os dados informados ja existe",
                details={"field": "isbn"},
            ) from exc

        await self._session.refresh(livro)
        return livro

    async def update(self, livro: Livro, payload: LivroUpdate) -> Livro:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(livro, field, value)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                status_code=409,
                code="livro_conflict",
                message="Livro com os dados informados ja existe",
                details={"field": "isbn"},
            ) from exc

        await self._session.refresh(livro)
        return livro

    async def delete(self, livro: Livro) -> None:
        await self._session.delete(livro)
        await self._session.commit()
