from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from app.dependencies import DBSession, CurrentUserID
from app.domain.users.repository import UserRepository
from app.domain.users.schemas import UserResponse
from .service import AuthService
from .schemas import LoginRequest, TokenResponse, RefreshRequest, AccessTokenResponse

router = APIRouter(prefix="/auth", tags=["Auth"])


def get_auth_service(db: DBSession) -> AuthService:
    return AuthService(UserRepository(db))


@router.post("/login", response_model=TokenResponse, summary="Login com email e senha")
async def login(
    data: LoginRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.login(data)


@router.post("/refresh", response_model=AccessTokenResponse, summary="Renovar access token")
async def refresh_token(
    data: RefreshRequest,
    service: AuthService = Depends(get_auth_service),
):
    return await service.refresh(data)