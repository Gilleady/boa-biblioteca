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
