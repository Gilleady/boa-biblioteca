from __future__ import annotations

from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.core.roles import ROLE_LEITOR, USER_ROLES
from app.schemas.common import PaginatedResponse


class UsuarioBase(BaseModel):
    pessoa_id: UUID = Field(description="Related pessoa id.")
    username: str = Field(
        min_length=3,
        max_length=80,
        description="Unique username.",
        examples=["adal"],
    )
    ativo: bool = Field(default=True, description="Whether the user account is active.")
    papel: Literal["admin", "atendente", "leitor"] = Field(
        default=ROLE_LEITOR,
        description="User role.",
        examples=list(USER_ROLES),
    )


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
    papel: Literal["admin", "atendente", "leitor"] | None = Field(
        default=None,
        description="User role.",
    )


class UsuarioRead(UsuarioBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID | None = None
    updated_by: UUID | None = None
    created_at: datetime
    updated_at: datetime | None = None


class UsuarioListResponse(PaginatedResponse[UsuarioRead]):
    pass
