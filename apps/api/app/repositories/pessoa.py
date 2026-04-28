from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.models.pessoa import Pessoa
from app.schemas.pessoa import PessoaCreate, PessoaUpdate


class PessoaRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        nome: str | None,
        email: str | None,
    ) -> tuple[list[Pessoa], int]:
        stmt: Select[tuple[Pessoa]] = select(Pessoa)

        if nome:
            stmt = stmt.where(Pessoa.nome.ilike(f"%{nome}%"))

        if email:
            stmt = stmt.where(Pessoa.email.ilike(f"%{email}%"))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        stmt = stmt.order_by(Pessoa.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, pessoa_id: UUID) -> Pessoa | None:
        result = await self._session.execute(
            select(Pessoa).where(Pessoa.id == pessoa_id)
        )
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Pessoa | None:
        result = await self._session.execute(
            select(Pessoa).where(Pessoa.email == email)
        )
        return result.scalar_one_or_none()

    async def exists_by_id(self, pessoa_id: UUID) -> bool:
        result = await self._session.execute(
            select(func.count()).select_from(Pessoa).where(Pessoa.id == pessoa_id)
        )
        return bool(result.scalar_one())

    async def create(self, payload: PessoaCreate, actor_id: UUID | None = None) -> Pessoa:
        pessoa = Pessoa(**payload.model_dump())
        if actor_id is not None:
            pessoa.created_by = actor_id
            pessoa.updated_by = actor_id
        self._session.add(pessoa)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                status_code=409,
                code="pessoa_conflict",
                message="Pessoa com os dados informados ja existe",
                details={"field": "email"},
            ) from exc

        await self._session.refresh(pessoa)
        return pessoa

    async def update(
        self,
        pessoa: Pessoa,
        payload: PessoaUpdate,
        actor_id: UUID | None = None,
    ) -> Pessoa:
        for field, value in payload.model_dump(exclude_unset=True).items():
            setattr(pessoa, field, value)

        if actor_id is not None:
            pessoa.updated_by = actor_id

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                status_code=409,
                code="pessoa_conflict",
                message="Pessoa com os dados informados ja existe",
                details={"field": "email"},
            ) from exc

        await self._session.refresh(pessoa)
        return pessoa

    async def delete(self, pessoa: Pessoa) -> None:
        await self._session.delete(pessoa)
        await self._session.commit()
