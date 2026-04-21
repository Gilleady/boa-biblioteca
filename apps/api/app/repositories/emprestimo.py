from __future__ import annotations

from datetime import datetime, timedelta
from typing import Literal
from uuid import UUID

from app.models.emprestimo import Emprestimo
from sqlalchemy import Select, asc, desc, func, select
from sqlalchemy.ext.asyncio import AsyncSession


class EmprestimoRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        pessoa_id: UUID | None,
        ativo: bool | None,
        order_by: Literal["created_at", "data_emprestimo"],
        order_direction: Literal["asc", "desc"],
    ) -> tuple[list[Emprestimo], int]:
        stmt: Select[tuple[Emprestimo]] = select(Emprestimo)

        if pessoa_id is not None:
            stmt = stmt.where(Emprestimo.pessoa_id == pessoa_id)

        if ativo is not None:
            stmt = stmt.where(Emprestimo.ativo.is_(ativo))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        order_column = {
            "created_at": Emprestimo.created_at,
            "data_emprestimo": Emprestimo.data_emprestimo,
        }[order_by]
        order_expression = (
            asc(order_column) if order_direction == "asc" else desc(order_column)
        )
        stmt = stmt.order_by(order_expression)
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, emprestimo_id: UUID) -> Emprestimo | None:
        result = await self._session.execute(
            select(Emprestimo).where(Emprestimo.id == emprestimo_id)
        )
        return result.scalar_one_or_none()

    async def get_active_by_pessoa(self, pessoa_id: UUID) -> Emprestimo | None:
        result = await self._session.execute(
            select(Emprestimo).where(
                (Emprestimo.pessoa_id == pessoa_id) & (Emprestimo.ativo.is_(True))
            )
        )
        return result.scalar_one_or_none()

    async def create(
        self, pessoa_id: UUID, livro_id: UUID, dias_emprestimo: int
    ) -> Emprestimo:
        now = datetime.now().astimezone()
        data_devolucao_prevista = now + timedelta(days=dias_emprestimo)

        emprestimo = Emprestimo(
            pessoa_id=pessoa_id,
            livro_id=livro_id,
            data_emprestimo=now,
            data_devolucao_prevista=data_devolucao_prevista,
        )
        self._session.add(emprestimo)
        await self._session.commit()
        await self._session.refresh(emprestimo)
        return emprestimo

    async def devolucao(self, emprestimo: Emprestimo) -> Emprestimo:
        emprestimo.data_devolucao_real = datetime.now().astimezone()
        emprestimo.ativo = False

        await self._session.commit()
        await self._session.refresh(emprestimo)
        return emprestimo
