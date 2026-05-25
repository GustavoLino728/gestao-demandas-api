import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.domain.lists.models import List


class ListRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, lst: List) -> List:
        self.session.add(lst)
        await self.session.flush()
        await self.session.refresh(lst)
        return lst

    async def create_many(self, lists: list[List]) -> list[List]:
        for lst in lists:
            self.session.add(lst)
        await self.session.flush()
        for lst in lists:
            await self.session.refresh(lst)
        return lists

    async def get_by_id(self, list_id: uuid.UUID) -> List | None:
        result = await self.session.execute(
            select(List).where(List.id == list_id)
        )
        return result.scalar_one_or_none()

    async def list_by_board(self, board_id: uuid.UUID) -> list[List]:
        result = await self.session.execute(
            select(List).where(List.board_id == board_id).order_by(List.position)
        )
        return list(result.scalars().all())

    async def delete(self, lst: List) -> None:
        await self.session.delete(lst)
        await self.session.flush()