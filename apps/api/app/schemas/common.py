from __future__ import annotations

from typing import TypeVar

from pydantic import BaseModel, Field

DataT = TypeVar("DataT")


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PaginatedResponse[DataT](BaseModel):
    items: list[DataT]
    total: int
    page: int
    page_size: int
