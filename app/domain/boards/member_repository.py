import uuid
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.domain.boards.models import BoardMember


class BoardMemberRepository:
    def __init__(self, session: AsyncSession):
        self.session = session

    async def create(self, member: BoardMember) -> BoardMember:
        self.session.add(member)
        await self.session.flush()
        await self.session.refresh(member)
        return member

    async def get_by_board_and_user(
        self, board_id: uuid.UUID, user_id: uuid.UUID
    ) -> BoardMember | None:
        result = await self.session.execute(
            select(BoardMember).where(
                BoardMember.board_id == board_id,
                BoardMember.user_id == user_id,
            )
        )
        return result.scalar_one_or_none()

    async def list_by_board(self, board_id: uuid.UUID) -> list[BoardMember]:
        result = await self.session.execute(
            select(BoardMember)
            .options(selectinload(BoardMember.user))
            .where(BoardMember.board_id == board_id)
            .order_by(BoardMember.added_at.asc())
        )
        return list(result.scalars().all())

    async def get_by_id(self, member_id: uuid.UUID) -> BoardMember | None:
        result = await self.session.execute(
            select(BoardMember)
            .options(selectinload(BoardMember.user))
            .where(BoardMember.id == member_id)
        )
        return result.scalar_one_or_none()

    async def delete(self, member: BoardMember) -> None:
        await self.session.delete(member)

    async def exists(self, board_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        member = await self.get_by_board_and_user(board_id, user_id)
        return member is not None