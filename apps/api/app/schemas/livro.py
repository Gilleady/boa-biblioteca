from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import PaginatedResponse
from pydantic import BaseModel, ConfigDict, Field


class LivroBase(BaseModel):
    titulo: str = Field(
        min_length=1,
        max_length=255,
        description="Book title.",
        examples=["Clean Code"],
    )
    autor: str = Field(
        min_length=1,
        max_length=255,
        description="Book author.",
        examples=["Robert C. Martin"],
    )
    isbn: str = Field(
        min_length=10,
        max_length=20,
        description="Book ISBN.",
        examples=["9780132350884"],
    )
    ano_publicacao: int | None = Field(
        default=None,
        ge=0,
        le=2100,
        description="Publication year.",
        examples=[2008],
    )
    disponivel: bool = Field(default=True, description="Availability status.")
    dias_emprestimo_padrao: int = Field(
        default=7,
        ge=1,
        le=365,
        description="Default loan duration in days.",
        examples=[7],
    )


class LivroCreate(LivroBase):
    pass


class LivroUpdate(BaseModel):
    titulo: str | None = Field(default=None, min_length=1, max_length=255)
    autor: str | None = Field(default=None, min_length=1, max_length=255)
    isbn: str | None = Field(default=None, min_length=10, max_length=20)
    ano_publicacao: int | None = Field(default=None, ge=0, le=2100)
    disponivel: bool | None = None
    dias_emprestimo_padrao: int | None = Field(default=None, ge=1, le=365)


class LivroRead(LivroBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime
    updated_at: datetime


class LivroListResponse(PaginatedResponse[LivroRead]):
    pass
