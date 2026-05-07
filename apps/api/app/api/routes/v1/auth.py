from datetime import UTC, datetime, timedelta
from secrets import randbelow
from typing import Literal, TypedDict, cast

from fastapi import APIRouter, Depends, Security, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_usuario
from app.api.docs import (
    AUTH_401_RESPONSE,
    CONFLICT_409_RESPONSE,
    INVALID_CREDENTIALS_401_RESPONSE,
    INVALID_PAYLOAD_400_RESPONSE,
    VALIDATION_422_RESPONSE,
)
from app.core.exceptions import AppError
from app.core.roles import ROLE_LEITOR
from app.core.security import create_access_token, verify_password
from app.db.session import get_async_session
from app.models.usuario import Usuario
from app.repositories.pessoa import PessoaRepository
from app.repositories.usuario import UsuarioRepository
from app.schemas.auth import (
    LoginRequest,
    RegisterRequest,
    RegisterResponse,
    RegisterVerifyRequest,
    TokenResponse,
)
from app.schemas.pessoa import PessoaCreate
from app.schemas.usuario import UsuarioCreate, UsuarioRead
from app.settings import get_settings

router = APIRouter(prefix="/auth", tags=["auth"])

_REGISTER_CODE_TTL_MINUTES = 10


class PendingRegisterData(TypedDict):
    pessoa_id: str
    username: str
    senha: str
    code: str
    expires_at: datetime


_pending_register_by_email: dict[str, PendingRegisterData] = {}


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


@router.post(
    "/register",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Public self-registration",
    description=(
        "Creates a leitor user immediately for a new email, or starts verification "
        "when the email already exists without a linked user."
    ),
    responses={
        409: CONFLICT_409_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def register(
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RegisterResponse:
    pessoa_repository = PessoaRepository(session)
    usuario_repository = UsuarioRepository(session)
    email = payload.email.strip().lower()

    existing_username = await usuario_repository.get_by_username(payload.username)
    if existing_username is not None:
        raise AppError(
            status_code=409,
            code="usuario_conflict",
            message="Usuario com os dados informados ja existe",
            details={"fields": ["username"]},
        )

    pessoa = await pessoa_repository.get_by_email(email)

    if pessoa is None:
        pessoa = await pessoa_repository.create(
            PessoaCreate(nome=payload.nome, email=email)
        )
        await usuario_repository.create(
            UsuarioCreate(
                pessoa_id=pessoa.id,
                username=payload.username,
                senha=payload.senha,
                ativo=True,
                papel=cast(Literal["admin", "atendente", "leitor"], ROLE_LEITOR),
            )
        )
        return RegisterResponse(
            status="created",
            message="Conta criada com sucesso.",
        )

    existing_user = await usuario_repository.get_by_pessoa_id(pessoa.id)
    if existing_user is not None:
        raise AppError(
            status_code=409,
            code="pessoa_already_has_user",
            message="Ja existe usuario vinculado para este email",
            details={"email": email},
        )

    code = f"{randbelow(1_000_000):06d}"
    expires_at = datetime.now(UTC) + timedelta(minutes=_REGISTER_CODE_TTL_MINUTES)
    _pending_register_by_email[email] = {
        "pessoa_id": str(pessoa.id),
        "username": payload.username,
        "senha": payload.senha,
        "code": code,
        "expires_at": expires_at,
    }

    settings = get_settings()
    return RegisterResponse(
        status="verification_required",
        message=(
            "Validacao por codigo necessaria para vincular usuario a pessoa existente."
        ),
        verification_code=code if settings.environment == "development" else None,
    )


@router.post(
    "/register/verify",
    response_model=RegisterResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Confirm self-registration email code",
    responses={
        400: INVALID_PAYLOAD_400_RESPONSE,
        409: CONFLICT_409_RESPONSE,
        422: VALIDATION_422_RESPONSE,
    },
)
async def register_verify(
    payload: RegisterVerifyRequest,
    session: AsyncSession = Depends(get_async_session),
) -> RegisterResponse:
    pessoa_repository = PessoaRepository(session)
    usuario_repository = UsuarioRepository(session)
    email = payload.email.strip().lower()
    pending = _pending_register_by_email.get(email)

    if pending is None:
        raise AppError(
            status_code=400,
            code="invalid_verification_code",
            message="Codigo de verificacao invalido ou expirado",
        )

    now = datetime.now(UTC)
    if pending["expires_at"] < now or pending["code"] != payload.code:
        _pending_register_by_email.pop(email, None)
        raise AppError(
            status_code=400,
            code="invalid_verification_code",
            message="Codigo de verificacao invalido ou expirado",
        )

    pessoa = await pessoa_repository.get_by_email(email)
    if pessoa is None:
        _pending_register_by_email.pop(email, None)
        raise AppError(
            status_code=404,
            code="pessoa_not_found",
            message="Pessoa nao encontrada",
            details={"email": email},
        )

    existing_user = await usuario_repository.get_by_pessoa_id(pessoa.id)
    if existing_user is not None:
        _pending_register_by_email.pop(email, None)
        raise AppError(
            status_code=409,
            code="pessoa_already_has_user",
            message="Ja existe usuario vinculado para este email",
            details={"email": email},
        )

    existing_username = await usuario_repository.get_by_username(pending["username"])
    if existing_username is not None:
        _pending_register_by_email.pop(email, None)
        raise AppError(
            status_code=409,
            code="usuario_conflict",
            message="Usuario com os dados informados ja existe",
            details={"fields": ["username"]},
        )

    await usuario_repository.create(
        UsuarioCreate(
            pessoa_id=pessoa.id,
            username=pending["username"],
            senha=pending["senha"],
            ativo=True,
            papel=cast(Literal["admin", "atendente", "leitor"], ROLE_LEITOR),
        )
    )
    _pending_register_by_email.pop(email, None)
    return RegisterResponse(
        status="created",
        message="Conta criada com sucesso.",
    )
