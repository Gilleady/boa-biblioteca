from __future__ import annotations

from uuid import UUID

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AppError
from app.core.security import hash_password
from app.models.usuario import Usuario
from app.schemas.usuario import UsuarioCreate, UsuarioUpdate


class UsuarioRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list(
        self,
        *,
        page: int,
        page_size: int,
        username: str | None,
        ativo: bool | None,
    ) -> tuple[list[Usuario], int]:
        stmt: Select[tuple[Usuario]] = select(Usuario)

        if username:
            stmt = stmt.where(Usuario.username.ilike(f"%{username}%"))

        if ativo is not None:
            stmt = stmt.where(Usuario.ativo.is_(ativo))

        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = int((await self._session.execute(count_stmt)).scalar_one())

        stmt = stmt.order_by(Usuario.created_at.desc())
        stmt = stmt.offset((page - 1) * page_size).limit(page_size)

        result = await self._session.execute(stmt)
        return list(result.scalars().all()), total

    async def get_by_id(self, usuario_id: UUID) -> Usuario | None:
        result = await self._session.execute(
            select(Usuario).where(Usuario.id == usuario_id)
        )
        return result.scalar_one_or_none()

    async def get_by_pessoa_id(self, pessoa_id: UUID) -> Usuario | None:
        result = await self._session.execute(
            select(Usuario).where(Usuario.pessoa_id == pessoa_id)
        )
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Usuario | None:
        result = await self._session.execute(
            select(Usuario).where(Usuario.username == username)
        )
        return result.scalar_one_or_none()

    async def create(
        self, payload: UsuarioCreate, actor_id: UUID | None = None
    ) -> Usuario:
        data = payload.model_dump()
        # Hash the senha before storing
        data["senha_hash"] = hash_password(data.pop("senha"))
        if actor_id is not None:
            data["created_by"] = actor_id
            data["updated_by"] = actor_id
        usuario = Usuario(**data)
        self._session.add(usuario)

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                status_code=409,
                code="usuario_conflict",
                message="Usuario com os dados informados ja existe",
                details={"fields": ["username", "pessoa_id"]},
            ) from exc

        await self._session.refresh(usuario)
        return usuario

    async def update(
        self,
        usuario: Usuario,
        payload: UsuarioUpdate,
        actor_id: UUID | None = None,
    ) -> Usuario:
        for field, value in payload.model_dump(exclude_unset=True).items():
            # Hash the senha if it's being updated
            if field == "senha" and value is not None:
                usuario.senha_hash = hash_password(value)
            else:
                setattr(usuario, field, value)

        if actor_id is not None:
            usuario.updated_by = actor_id

        try:
            await self._session.commit()
        except IntegrityError as exc:
            await self._session.rollback()
            raise AppError(
                status_code=409,
                code="usuario_conflict",
                message="Usuario com os dados informados ja existe",
                details={"fields": ["username", "pessoa_id"]},
            ) from exc

        await self._session.refresh(usuario)
        return usuario

    async def delete(self, usuario: Usuario) -> None:
        await self._session.delete(usuario)
        await self._session.commit()
