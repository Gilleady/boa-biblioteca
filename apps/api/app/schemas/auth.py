from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request body for user login."""

    username: str = Field(min_length=3, max_length=80)
    senha: str = Field(min_length=1, max_length=255)


class TokenResponse(BaseModel):
    """Response body for authentication token."""

    access_token: str
    token_type: str = "bearer"
