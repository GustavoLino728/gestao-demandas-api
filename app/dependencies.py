from typing import Annotated
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.core.context import set_current_user_id
from app.core.exceptions import credentials_exception
from app.core.security import decode_token

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

DBSession = Annotated[AsyncSession, Depends(get_db)]
TokenDep = Annotated[str, Depends(oauth2_scheme)]


async def get_current_user_id(token: TokenDep) -> int:
    try:
        payload = decode_token(token)
        if payload.get("type") != "access":
            raise credentials_exception
        user_id = int(payload["sub"])

        set_current_user_id(user_id)

        return user_id
    except (JWTError, ValueError):
        raise credentials_exception


CurrentUserID = Annotated[int, Depends(get_current_user_id)]