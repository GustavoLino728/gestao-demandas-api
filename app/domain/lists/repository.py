import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.lists.models import List


class ListRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, lst: List) -> List:
        self.db.add(lst)
        await self.db.flush()
        await self.db.refresh(lst)
        return lst

    async def create_many(self, lists: list[List]) -> list[List]:
        for lst in lists:
            self.db.add(lst)
        await self.db.flush()
        for lst in lists:
            await self.db.refresh(lst)
        return lists

    async def get_by_id(self, list_id: uuid.UUID) -> List | None:
        result = await self.db.execute(select(List).where(List.id == list_id))
        return result.scalar_one_or_none()

    async def list_by_board(self, board_id: uuid.UUID) -> list[List]:
        result = await self.db.execute(
            select(List).where(List.board_id == board_id).order_by(List.position)
        )
        return list(result.scalars().all())

    async def delete(self, lst: List) -> None:
        await self.db.delete(lst)