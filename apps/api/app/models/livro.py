from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from app.db.base import Base
from sqlalchemy import Boolean, DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column


class Livro(Base):
    __tablename__ = "livros"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    titulo: Mapped[str] = mapped_column(String(255), nullable=False)
    autor: Mapped[str] = mapped_column(String(255), nullable=False)
    isbn: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    ano_publicacao: Mapped[int | None] = mapped_column(Integer)
    disponivel: Mapped[bool] = mapped_column(Boolean, nullable=False, default=True)
    dias_emprestimo_padrao: Mapped[int] = mapped_column(
        Integer, nullable=False, default=7
    )
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
