from __future__ import annotations

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Pessoa(Base):
    __tablename__ = "pessoas"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    nome: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    created_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", use_alter=True), nullable=True
    )
    updated_by: Mapped[UUID | None] = mapped_column(
        ForeignKey("usuarios.id", use_alter=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        onupdate=func.now(),
    )
