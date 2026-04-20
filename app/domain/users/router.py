from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.dependencies import DBSession, AdminOnly, GestorOrAbove, AnyUser
from .service import UserService
from .repository import UserRepository
from .schemas import UserCreate, UserUpdate, UserAdminUpdate, UserResponse
from .models import UserRole

router = APIRouter(prefix="/users", tags=["Users"])


def get_user_service(db: DBSession) -> UserService:
    return UserService(UserRepository(db))


@router.post(
    "/",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Criar usuário",
)
async def create_user(
    data: UserCreate,
    service: UserService = Depends(get_user_service),
):
    return await service.create_user(data)


@router.get(
    "/me",
    response_model=UserResponse,
    summary="Dados do usuário autenticado",
)
async def get_me(
    current_user_id: AnyUser,
    service: UserService = Depends(get_user_service),
):
    return await service.get_user_or_404(current_user_id)


@router.patch(
    "/me",
    response_model=UserResponse,
    summary="Atualizar próprio perfil",
)
async def update_me(
    data: UserUpdate,
    current_user_id: AnyUser,
    service: UserService = Depends(get_user_service),
):
    return await service.update_me(current_user_id, data)


@router.get(
    "/",
    response_model=list[UserResponse],
    summary="Listar usuários ativos",
)
async def list_users(
    limit: int = 20,
    offset: int = 0,
    current_user_id: AnyUser = None,
    service: UserService = Depends(get_user_service),
):
    return await service.list_users(limit=limit, offset=offset)


@router.get(
    "/{user_id}",
    response_model=UserResponse,
    summary="Buscar usuário por ID",
)
async def get_user(
    user_id: int,
    current_user_id: AnyUser,
    service: UserService = Depends(get_user_service),
):
    return await service.get_user_or_404(user_id)


@router.patch(
    "/{user_id}/admin",
    response_model=UserResponse,
    summary="[ADMIN] Alterar role, status ou verificação",
)
async def admin_update_user(
    user_id: int,
    data: UserAdminUpdate,
    current_user_id: AnyUser,
    service: UserService = Depends(get_user_service),
    db: DBSession = None,
):
    requester = await service.get_user_or_404(current_user_id)
    return await service.admin_update(user_id, data, requester.role)


@router.delete(
    "/{user_id}",
    response_model=UserResponse,
    summary="[ADMIN] Desativar usuário",
)
async def deactivate_user(
    user_id: int,
    current_user_id: AnyUser,
    service: UserService = Depends(get_user_service),
):
    requester = await service.get_user_or_404(current_user_id)
    return await service.deactivate(user_id, requester.role)