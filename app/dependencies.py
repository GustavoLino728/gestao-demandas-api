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


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
) -> uuid.UUID:
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        sub = payload.get("sub")
        if not sub:
            raise credentials_exception
        return uuid.UUID(sub)
    except (JWTError, ValueError) as e:
        logger.error(f"ERRO AO DECODIFICAR: {type(e).__name__}: {e}")
        raise credentials_exception


async def get_current_user_role(
    credentials: HTTPAuthorizationCredentials = Security(http_bearer),
) -> tuple[uuid.UUID, str]:
    try:
        token = credentials.credentials
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        sub = payload.get("sub")
        role = payload.get("role", "")
        if not sub:
            raise credentials_exception
        return uuid.UUID(sub), role
    except (JWTError, ValueError):
        raise credentials_exception


def require_role(*roles: UserRole):
    async def _check(
        credentials: HTTPAuthorizationCredentials = Security(http_bearer),
    ) -> uuid.UUID:
        try:
            token = credentials.credentials
            payload = decode_token(token)
            sub = payload.get("sub")
            role = payload.get("role", "")
            if not sub or role not in [r.value for r in roles]:
                raise ForbiddenError()
            return uuid.UUID(sub)
        except (JWTError, ValueError):
            raise credentials_exception
    return _check


CurrentUserID = Annotated[uuid.UUID, Depends(get_current_user_id)]
AdminOnly = Annotated[uuid.UUID, Depends(require_role(UserRole.ADMIN))]