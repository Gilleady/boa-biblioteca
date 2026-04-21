from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_usuario
from app.api.docs import (
    AUTH_401_RESPONSE,
    INVALID_CREDENTIALS_401_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.exceptions import AppError
from app.core.security import create_access_token, verify_password
from app.db.session import get_async_session
from app.models.usuario import Usuario
from app.repositories.usuario import UsuarioRepository
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.usuario import UsuarioRead

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/login",
    response_model=TokenResponse,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user",
    description="Validates username/senha and returns a JWT bearer token.",
    responses={401: INVALID_CREDENTIALS_401_RESPONSE, 422: VALIDATION_422_RESPONSE},
)
async def login(
    payload: LoginRequest,
    session: AsyncSession = Depends(get_async_session),
) -> TokenResponse:
    """Authenticate user and return JWT access token."""
    repository = UsuarioRepository(session)

    # Search for usuario by username
    usuarios, _ = await repository.list(
        page=1, page_size=1, username=payload.username, ativo=None
    )

    if not usuarios:
        raise AppError(
            status_code=401,
            code="invalid_credentials",
            message="Invalid username or password",
        )

    usuario = usuarios[0]

    # Verify password
    if not verify_password(payload.senha, usuario.senha_hash):
        raise AppError(
            status_code=401,
            code="invalid_credentials",
            message="Invalid username or password",
        )

    # Generate token
    access_token = create_access_token(usuario.id)

    return TokenResponse(access_token=access_token, token_type="bearer")


@router.get(
    "/me",
    response_model=UsuarioRead,
    summary="Get current authenticated user",
    description="Returns the authenticated user based on the bearer token.",
    responses={401: AUTH_401_RESPONSE},
)
async def me(usuario: Usuario = Security(get_current_usuario)) -> UsuarioRead:
    return UsuarioRead.model_validate(usuario)
