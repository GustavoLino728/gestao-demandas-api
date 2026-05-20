import uuid
from datetime import datetime, timezone
from app.core.exceptions import NotFoundError, ForbiddenError
from app.domain.users.models import UserRole
from .models import Card, CardHistory
from .repository import CardRepository
from .schemas import CardCreate, CardUpdate, CardMove


class CardService:
    def __init__(self, repository: CardRepository):
        self.repo = repository

    async def create_card(self, data: CardCreate, current_user_id: uuid.UUID) -> Card:
        count = await self.repo.count_by_list(data.list_id)
        card = Card(
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
            list_id=data.list_id,
            assignee_id=data.assignee_id,
            position=count,   # insere sempre no final da lista
        )
        created = await self.repo.create(card)
        await self._record_history(
            card_id=created.id,
            changed_by=current_user_id,
            field="title",
            old_value=None,
            new_value=created.title,
        )
        return created

    async def get_card(self, card_id: uuid.UUID) -> Card:
        card = await self.repo.get_by_id_with_history(card_id)
        if not card:
            raise NotFoundError(f"Card {card_id} não encontrado")
        return card

    async def list_by_list(self, list_id: uuid.UUID) -> list[Card]:
        return await self.repo.get_by_list(list_id)

    async def list_by_assignee(self, user_id: uuid.UUID) -> list[Card]:
        return await self.repo.get_by_assignee(user_id)

    async def update_card(
        self,
        card_id: uuid.UUID,
        data: CardUpdate,
        current_user_id: uuid.UUID,
        current_user_role: UserRole,
    ) -> Card:
        card = await self.repo.get_by_id(card_id)
        if not card:
            raise NotFoundError(f"Card {card_id} não encontrado")

        is_assignee = card.assignee_id == current_user_id
        is_privileged = current_user_role in (UserRole.GESTOR, UserRole.ADMIN)

        if not is_assignee and not is_privileged:
            raise ForbiddenError("Apenas o responsável ou gestores podem editar este card")

        changes = data.model_dump(exclude_unset=True)

        for field, new_value in changes.items():
            old_value = getattr(card, field)
            if old_value != new_value:
                await self._record_history(
                    card_id=card.id,
                    changed_by=current_user_id,
                    field=field,
                    old_value=str(old_value) if old_value is not None else None,
                    new_value=str(new_value),
                )
                setattr(card, field, new_value)

        await self.repo.session.flush()
        return card

    async def move_card(
        self, card_id: uuid.UUID, data: CardMove, current_user_id: uuid.UUID
    ) -> Card:
        card = await self.repo.get_by_id(card_id)
        if not card:
            raise NotFoundError(f"Card {card_id} não encontrado")

        old_list_id = card.list_id
        old_position = card.position

        # Libera a posição antiga
        await self.repo.reorder_after_removal(old_list_id, old_position)

        # Abre espaço na nova posição
        await self.repo.make_room_at(data.list_id, data.position)

        # Registra no histórico se mudou de lista
        if old_list_id != data.list_id:
            await self._record_history(
                card_id=card.id,
                changed_by=current_user_id,
                field="list_id",
                old_value=str(old_list_id),
                new_value=str(data.list_id),
            )

        card.list_id = data.list_id
        card.position = data.position
        await self.repo.session.flush()
        return card

    async def delete_card(
        self,
        card_id: uuid.UUID,
        current_user_role: UserRole,
    ) -> None:
        card = await self.repo.get_by_id(card_id)
        if not card:
            raise NotFoundError(f"Card {card_id} não encontrado")

        if current_user_role not in (UserRole.GESTOR, UserRole.ADMIN):
            raise ForbiddenError("Apenas gestores e admins podem deletar cards")

        old_position = card.position
        old_list_id = card.list_id
        await self.repo.delete(card)
        await self.repo.reorder_after_removal(old_list_id, old_position)

    async def _record_history(
        self,
        card_id: uuid.UUID,
        changed_by: uuid.UUID,
        field: str,
        old_value: str | None,
        new_value: str | None,
    ) -> None:
        entry = CardHistory(
            card_id=card_id,
            changed_by=changed_by,
            field_changed=field,
            old_value=old_value,
            new_value=new_value,
            changed_at=datetime.now(timezone.utc),
        )
        await self.repo.add_history(entry)