from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedResponse


class PessoaBase(BaseModel):
    nome: str = Field(
        min_length=1,
        max_length=255,
        description="Full name.",
        examples=["Ada Lovelace"],
    )
    email: str = Field(
        min_length=3,
        max_length=255,
        description="Email address.",
        examples=["ada@example.com"],
    )


class PessoaCreate(PessoaBase):
    pass


class PessoaUpdate(BaseModel):
    nome: str | None = Field(default=None, min_length=1, max_length=255)
    email: str | None = Field(default=None, min_length=3, max_length=255)


class PessoaRead(PessoaBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID | None = None
    updated_by: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None


class PessoaListResponse(PaginatedResponse[PessoaRead]):
    pass
