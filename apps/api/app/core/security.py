from datetime import UTC, datetime, timedelta
from uuid import UUID

from jose import JWTError, jwt  # type: ignore[import-untyped]
from passlib.context import CryptContext  # type: ignore[import-untyped]

from app.settings import get_settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    """Hash a plain password using bcrypt."""
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed password."""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(usuario_id: UUID, expires_in: timedelta | None = None) -> str:
    """Create a JWT access token for a usuario."""
    settings = get_settings()

    if expires_in is None:
        expires_in = timedelta(minutes=settings.jwt_expiration_minutes)

    expire = datetime.now(UTC) + expires_in
    to_encode = {"sub": str(usuario_id), "exp": expire}

    encoded_jwt = jwt.encode(
        to_encode, settings.jwt_secret_key, algorithm=settings.jwt_algorithm
    )
    return encoded_jwt


def decode_access_token(token: str) -> UUID | None:
    """Decode a JWT access token and return the usuario_id."""
    settings = get_settings()

    try:
        payload = jwt.decode(
            token, settings.jwt_secret_key, algorithms=[settings.jwt_algorithm]
        )
        usuario_id: str | None = payload.get("sub")
        if usuario_id is None:
            return None
        return UUID(usuario_id)
    except (JWTError, ValueError):
        return None
