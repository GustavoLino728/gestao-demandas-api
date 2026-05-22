import uuid
from sqlalchemy import select, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.shared.base_repository import BaseRepository
from app.domain.boards.models import Board, BoardMember


class BoardRepository(BaseRepository[Board]):
    def __init__(self, session: AsyncSession):
        super().__init__(Board, session)

    async def create(self, board: Board) -> Board:
        self.session.add(board)
        await self.session.flush()
        await self.session.refresh(board)
        return board

    async def get_by_id(self, board_id: uuid.UUID) -> Board | None:
        result = await self.session.execute(
            select(Board).where(Board.id == board_id)
        )
        return result.scalar_one_or_none()

    async def get_by_id_with_lists(self, board_id: uuid.UUID) -> Board | None:
        result = await self.session.execute(
            select(Board)
            .where(Board.id == board_id)
            .options(selectinload(Board.lists))
        )
        return result.scalar_one_or_none()

    async def list_by_owner(self, owner_id: uuid.UUID) -> list[Board]:
        result = await self.session.execute(
            select(Board).where(Board.owner_id == owner_id)
        )
        return list(result.scalars().all())

    async def delete(self, board: Board) -> None:
        await self.session.delete(board)
        await self.session.flush()

    async def list_all(self) -> list[Board]:
        result = await self.session.execute(
            select(Board).order_by(Board.created_at.desc())
        )
        return list(result.scalars().all())

    async def list_visible_for_user(self, user_id: uuid.UUID) -> list[Board]:
        result = await self.session.execute(
            select(Board)
            .outerjoin(BoardMember, BoardMember.board_id == Board.id)
            .where(
                or_(
                    Board.owner_id == user_id,
                    BoardMember.user_id == user_id,
                )
            )
            .distinct()
            .order_by(Board.created_at.desc())
        )
        return list(result.scalars().all())

    async def user_has_access(self, board_id: uuid.UUID, user_id: uuid.UUID) -> bool:
        result = await self.session.execute(
            select(Board.id)
            .outerjoin(BoardMember, BoardMember.board_id == Board.id)
            .where(
                Board.id == board_id,
                or_(
                    Board.owner_id == user_id,
                    BoardMember.user_id == user_id,
                ),
            )
        )
        return result.scalar_one_or_none() is not None