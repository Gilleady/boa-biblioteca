from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    """Request body for user login."""

    username: str = Field(
        min_length=3,
        max_length=80,
        description="Username used to authenticate the user.",
        examples=["adal"],
    )
    senha: str = Field(
        min_length=1,
        max_length=255,
        description="User password in plain text.",
        examples=["senha123"],
    )


class TokenResponse(BaseModel):
    """Response body for authentication token."""

    access_token: str = Field(description="JWT access token.")
    token_type: str = Field(default="bearer", description="Authentication token type.")


class RegisterRequest(BaseModel):
    nome: str = Field(min_length=1, max_length=255, description="Person full name.")
    email: str = Field(min_length=3, max_length=255, description="Person email.")
    username: str = Field(min_length=3, max_length=80, description="Desired username.")
    senha: str = Field(min_length=1, max_length=255, description="Desired password.")


class RegisterResponse(BaseModel):
    status: str = Field(description="Registration status.")
    message: str = Field(description="Human-readable status message.")
    verification_code: str | None = Field(
        default=None,
        description="Development-only verification code preview.",
    )


class RegisterVerifyRequest(BaseModel):
    email: str = Field(min_length=3, max_length=255, description="Person email.")
    code: str = Field(
        min_length=6,
        max_length=6,
        description="Email verification code.",
    )
