import uuid
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from app.shared.base_repository import BaseRepository
from .models import Card, CardHistory


class CardRepository(BaseRepository[Card]):
    def __init__(self, session: AsyncSession):
        super().__init__(Card, session)

    async def get_by_id_with_history(self, card_id: uuid.UUID) -> Card | None:
        result = await self.session.execute(
            select(Card)
            .options(selectinload(Card.history))
            .where(Card.id == card_id)
        )
        return result.scalar_one_or_none()

    async def get_by_list(self, list_id: uuid.UUID) -> list[Card]:
        result = await self.session.execute(
            select(Card)
            .where(Card.list_id == list_id)
            .order_by(Card.position)
        )
        return list(result.scalars().all())

    async def get_by_assignee(self, user_id: uuid.UUID) -> list[Card]:
        result = await self.session.execute(
            select(Card)
            .where(Card.assignee_id == user_id)
            .order_by(Card.created_at.desc())
        )
        return list(result.scalars().all())

    async def count_by_list(self, list_id: uuid.UUID) -> int:
        result = await self.session.execute(
            select(func.count()).where(Card.list_id == list_id)
        )
        return result.scalar_one()

    async def reorder_after_removal(
        self, list_id: uuid.UUID, removed_position: int
    ) -> None:
        """Decrementa position de todos os cards após a posição removida."""
        result = await self.session.execute(
            select(Card)
            .where(Card.list_id == list_id, Card.position > removed_position)
        )
        for card in result.scalars().all():
            card.position -= 1

    async def make_room_at(self, list_id: uuid.UUID, position: int) -> None:
        """Incrementa position de todos os cards a partir da posição alvo."""
        result = await self.session.execute(
            select(Card)
            .where(Card.list_id == list_id, Card.position >= position)
        )
        for card in result.scalars().all():
            card.position += 1

    async def add_history(self, entry: CardHistory) -> None:
        self.session.add(entry)