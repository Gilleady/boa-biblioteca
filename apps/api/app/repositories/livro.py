from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import Select, asc, desc, func, select
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
        autor: str | None,
        ano_publicacao: int | None,
        disponivel: bool | None,
        order_by: Literal["created_at", "titulo", "ano_publicacao"],
        order_direction: Literal["asc", "desc"],
    ) -> tuple[list[Livro], int]:
        stmt: Select[tuple[Livro]] = select(Livro)

        if titulo:
            stmt = stmt.where(Livro.titulo.ilike(f"%{titulo}%"))

        if autor:
            stmt = stmt.where(Livro.autor.ilike(f"%{autor}%"))

        if ano_publicacao is not None:
            stmt = stmt.where(Livro.ano_publicacao == ano_publicacao)

        if disponivel is not None:
            stmt = stmt.where(Livro.disponivel.is_(disponivel))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        order_column = {
            "created_at": Livro.created_at,
            "titulo": Livro.titulo,
            "ano_publicacao": Livro.ano_publicacao,
        }[order_by]
        order_expression = (
            asc(order_column) if order_direction == "asc" else desc(order_column)
        )
        stmt = stmt.order_by(order_expression)
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
