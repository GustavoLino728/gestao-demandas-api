from app.core.exceptions import ConflictError, NotFoundError, ForbiddenError
from app.core.security import hash_password
from .models import User, UserRole
from .repository import UserRepository
from .schemas import UserCreate, UserUpdate, UserAdminUpdate


class UserService:
    def __init__(self, repository: UserRepository):
        self.repo = repository

    async def create_user(self, data: UserCreate) -> User:
        if await self.repo.get_by_email(data.email):
            raise ConflictError(f"Email '{data.email}' já está em uso")

        if await self.repo.get_by_registration(data.registration):
            raise ConflictError(f"Matrícula '{data.registration}' já está cadastrada")

        user = User(
            email=data.email,
            password_hash=hash_password(data.password),
            full_name=data.full_name,
            registration=data.registration,
            sector=data.sector,
            position=data.position,
            phone=data.phone,
            role=data.role,
        )
        return await self.repo.create(user)

    async def get_user_or_404(self, user_id: int) -> User:
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise NotFoundError(f"Usuário {user_id} não encontrado")
        return user

    async def update_me(self, user_id: int, data: UserUpdate) -> User:
        user = await self.get_user_or_404(user_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        await self.repo.session.flush()
        return user

    async def admin_update(
        self, target_id: int, data: UserAdminUpdate, requester_role: UserRole
    ) -> User:
        if requester_role != UserRole.ADMIN:
            raise ForbiddenError("Apenas administradores podem alterar role e status")

        user = await self.get_user_or_404(target_id)
        for field, value in data.model_dump(exclude_none=True).items():
            setattr(user, field, value)
        await self.repo.session.flush()
        return user

    async def deactivate(self, target_id: int, requester_role: UserRole) -> User:
        if requester_role != UserRole.ADMIN:
            raise ForbiddenError("Apenas administradores podem desativar usuários")
        user = await self.get_user_or_404(target_id)
        user.is_active = False
        await self.repo.session.flush()
        return user

    async def list_users(self, limit: int = 20, offset: int = 0) -> list[User]:
        return await self.repo.get_active_users(limit=limit, offset=offset)