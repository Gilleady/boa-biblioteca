from typing import Callable, Coroutine, Any
from uuid import UUID

from fastapi import Depends, HTTPException, Security, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.roles import ROLE_ADMIN, ROLE_ATENDENTE, ROLE_LEITOR
from app.core.security import decode_access_token
from app.db.session import get_async_session
from app.models.usuario import Usuario
from app.repositories.usuario import UsuarioRepository

bearer_scheme = HTTPBearer(auto_error=False, scheme_name="BearerAuth")


async def get_current_usuario(
    session: AsyncSession = Depends(get_async_session),
    credentials: HTTPAuthorizationCredentials | None = Security(bearer_scheme),
) -> Usuario:
    """Extract and validate JWT token, return current usuario."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    usuario_id = decode_access_token(token)
    if usuario_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    repository = UsuarioRepository(session)
    usuario = await repository.get_by_id(usuario_id)

    if usuario is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario not found",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if not usuario.ativo:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuario is inactive",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return usuario


def require_roles(*allowed_roles: str) -> Callable[..., Coroutine[Any, Any, Usuario]]:
    async def dependency(usuario: Usuario = Security(get_current_usuario)) -> Usuario:
        if usuario.papel not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions",
            )
        return usuario

    return dependency


get_admin_or_atendente = require_roles(ROLE_ADMIN, ROLE_ATENDENTE)
get_leitor = require_roles(ROLE_LEITOR)


def resolve_emprestimo_scope_pessoa_id(
    *,
    usuario: Usuario,
    requested_pessoa_id: UUID | None,
) -> UUID | None:
    if usuario.papel != ROLE_LEITOR:
        return requested_pessoa_id

    if requested_pessoa_id is not None and requested_pessoa_id != usuario.pessoa_id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Leitor can only access own loans",
        )

    return usuario.pessoa_id
