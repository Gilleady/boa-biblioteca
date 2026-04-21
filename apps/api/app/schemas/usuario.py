from __future__ import annotations

from datetime import datetime
from uuid import UUID

from app.schemas.common import PaginatedResponse
from pydantic import BaseModel, ConfigDict, Field


class UsuarioBase(BaseModel):
    pessoa_id: UUID
    username: str = Field(min_length=3, max_length=80)
    ativo: bool = True


class UsuarioCreate(UsuarioBase):
    senha: str = Field(min_length=1, max_length=255)


class UsuarioUpdate(BaseModel):
    pessoa_id: UUID | None = None
    username: str | None = Field(default=None, min_length=3, max_length=80)
    senha: str | None = Field(default=None, min_length=1, max_length=255)
    ativo: bool | None = None


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_at: datetime


class UsuarioListResponse(PaginatedResponse[UsuarioRead]):
    pass
