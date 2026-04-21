from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import PaginatedResponse
from pydantic import BaseModel, ConfigDict, Field


class UsuarioBase(BaseModel):
    pessoa_id: UUID = Field(description="Related pessoa id.")
    username: str = Field(
        min_length=3,
        max_length=80,
        description="Unique username.",
        examples=["adal"],
    )
    ativo: bool = Field(default=True, description="Whether the user account is active.")


class UsuarioCreate(UsuarioBase):
    senha: str = Field(
        min_length=1,
        max_length=255,
        description="User password in plain text.",
        examples=["senha123"],
    )


class UsuarioUpdate(BaseModel):
    pessoa_id: UUID | None = Field(default=None, description="Related pessoa id.")
    username: str | None = Field(default=None, min_length=3, max_length=80)
    senha: str | None = Field(default=None, min_length=1, max_length=255)
    ativo: bool | None = None


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class UsuarioListResponse(PaginatedResponse[UsuarioRead]):
    pass
