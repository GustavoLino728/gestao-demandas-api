import uuid
from jose import JWTError
from app.core.security import verify_password, create_access_token, create_refresh_token, decode_token
from app.core.exceptions import UnauthorizedError
from app.domain.users.repository import UserRepository
from app.domain.users.models import User
from .schemas import LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse


class AuthService:
    def __init__(self, user_repo: UserRepository):
        self.user_repo = user_repo

    async def login(self, data: LoginRequest) -> TokenResponse:
        user = await self.user_repo.get_by_email(data.email)

        if not user or not verify_password(data.password, user.password_hash):
            raise UnauthorizedError("Email ou senha inválidos")

        if not user.is_active:
            raise UnauthorizedError("Conta desativada. Entre em contato com o administrador")

        extra = {"role": user.role, "email": user.email}
        return TokenResponse(
            access_token=create_access_token(subject=str(user.id), extra_data=extra),
            refresh_token=create_refresh_token(subject=str(user.id)),
        )

    async def refresh(self, data: RefreshRequest) -> AccessTokenResponse:
        try:
            payload = decode_token(data.refresh_token)

            if payload.get("type") != "refresh":
                raise UnauthorizedError("Token inválido")

            user_id = uuid.UUID(payload["sub"])
            user = await self.user_repo.get_by_id(user_id)

            if not user or not user.is_active:
                raise UnauthorizedError("Usuário não encontrado ou inativo")

            extra = {"role": user.role, "email": user.email}
            return AccessTokenResponse(
                access_token=create_access_token(subject=str(user.id), extra_data=extra)
            )

        except (JWTError, ValueError, KeyError):
            raise UnauthorizedError("Refresh token inválido ou expirado")

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        user = await self.user_repo.get_by_id(user_id)
        if not user or not user.is_active:
            raise UnauthorizedError("Usuário não encontrado")
        return user