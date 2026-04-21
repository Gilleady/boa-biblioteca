from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from app.db.base import Base
from sqlalchemy import Boolean, DateTime, ForeignKey, func
from sqlalchemy.orm import Mapped, mapped_column


class Emprestimo(Base):
    __tablename__ = "emprestimos"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    pessoa_id: Mapped[UUID] = mapped_column(
        ForeignKey("pessoas.id"), nullable=False, index=True
    )
    livro_id: Mapped[UUID] = mapped_column(
        ForeignKey("livros.id"), nullable=False, index=True
    )
    data_emprestimo: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    data_devolucao_prevista: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False
    )
    data_devolucao_real: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    ativo: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
