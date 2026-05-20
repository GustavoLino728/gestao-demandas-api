import uuid
from typing import Annotated
from fastapi import Depends, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.exceptions import credentials_exception, ForbiddenError
from app.core.security import decode_token
from app.domain.users.models import UserRole


http_bearer = HTTPBearer(auto_error=True)
DBSession = Annotated[AsyncSession, Depends(get_db)]


async def _extract_payload(
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
) -> dict:
    try:
        payload = decode_token(credentials.credentials)
        if payload.get("type") != "access":
            raise credentials_exception
        if not payload.get("sub"):
            raise credentials_exception
        return payload
    except (JWTError, ValueError):
        raise credentials_exception


async def get_current_user_id(
    payload: Annotated[dict, Depends(_extract_payload)],
) -> uuid.UUID:
    return uuid.UUID(payload["sub"])

async def get_current_user_context(
    payload: Annotated[dict, Depends(_extract_payload)],
) -> tuple[uuid.UUID, UserRole]:
    """Retorna (user_id, role) sem bater no banco."""
    return uuid.UUID(payload["sub"]), UserRole(payload.get("role", "servidor"))

CurrentUserContext = Annotated[
    tuple[uuid.UUID, UserRole], Depends(get_current_user_context)
]

def require_roles(*allowed: UserRole):
    async def _guard(
        payload: Annotated[dict, Depends(_extract_payload)],
    ) -> uuid.UUID:
        role = payload.get("role", "")
        if role not in [r.value for r in allowed]:
            raise ForbiddenError(
                f"Acesso restrito. Perfis permitidos: {[r.value for r in allowed]}"
            )
        return uuid.UUID(payload["sub"])
    return _guard

CurrentUserID  = Annotated[uuid.UUID, Depends(get_current_user_id)]
AnyUser        = CurrentUserID
AdminOnly      = Annotated[uuid.UUID, Depends(require_roles(UserRole.ADMIN))]
GestorOrAbove  = Annotated[uuid.UUID, Depends(require_roles(UserRole.ADMIN, UserRole.GESTOR))]