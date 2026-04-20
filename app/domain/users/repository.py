from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.shared.base_repository import BaseRepository
from .models import User


class UserRepository(BaseRepository[User]):
    def __init__(self, session: AsyncSession):
        super().__init__(User, session)

    async def get_by_email(self, email: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()

    async def get_by_registration(self, registration: str) -> User | None:
        result = await self.session.execute(
            select(User).where(User.registration == registration)
        )
        return result.scalar_one_or_none()

    async def get_active_users(self, limit: int = 20, offset: int = 0) -> list[User]:
        result = await self.session.execute(
            select(User)
            .where(User.is_active == True)
            .order_by(User.full_name)
            .limit(limit)
            .offset(offset)
        )
        return list(result.scalars().all())