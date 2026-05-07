from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field


class ErrorBody(BaseModel):
    code: str = Field(examples=["invalid_credentials"])
    message: str = Field(examples=["Invalid username or password"])
    details: dict[str, Any] | list[dict[str, Any]] = Field(default_factory=dict)


class ErrorResponse(BaseModel):
    error: ErrorBody


class ValidationErrorItem(BaseModel):
    loc: list[str] = Field(examples=[["body", "username"]])
    msg: str = Field(examples=["Field required"])
    type: str = Field(examples=["missing"])


class ValidationErrorBody(BaseModel):
    code: str = Field(default="validation_error")
    message: str = Field(default="Request validation failed")
    details: list[ValidationErrorItem]


class ValidationErrorResponse(BaseModel):
    error: ValidationErrorBody
