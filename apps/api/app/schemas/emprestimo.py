from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.common import PaginatedResponse


class EmprestimoBase(BaseModel):
    pessoa_id: UUID = Field(description="ID of the person borrowing the book.")
    livro_id: UUID = Field(description="ID of the book being borrowed.")


class EmprestimoCreate(EmprestimoBase):
    pass


class EmprestimoDevolver(BaseModel):
    pass


class EmprestimoRead(EmprestimoBase):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    created_by: UUID | None = None
    updated_by: UUID | None = None
    data_emprestimo: datetime
    data_devolucao_prevista: datetime
    data_devolucao_real: datetime | None
    ativo: bool
    created_at: datetime
    updated_at: datetime


class EmprestimoListResponse(PaginatedResponse[EmprestimoRead]):
    pass
