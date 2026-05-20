import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from .models import CardPriority


class CardCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    description: str | None = None
    priority: CardPriority = CardPriority.MEDIUM
    due_date: datetime | None = None
    list_id: uuid.UUID
    assignee_id: uuid.UUID | None = None


class CardUpdate(BaseModel):
    title: str | None = Field(None, min_length=1, max_length=255)
    description: str | None = None
    priority: CardPriority | None = None
    due_date: datetime | None = None
    assignee_id: uuid.UUID | None = None


class CardMove(BaseModel):
    """Payload para mover card entre listas ou reordenar."""
    list_id: uuid.UUID
    position: int = Field(..., ge=0)


class CardHistoryResponse(BaseModel):
    id: uuid.UUID
    field_changed: str
    old_value: str | None
    new_value: str | None
    changed_by: uuid.UUID | None
    changed_at: datetime

    model_config = {"from_attributes": True}


class CardResponse(BaseModel):
    id: uuid.UUID
    title: str
    description: str | None
    priority: CardPriority
    position: int
    due_date: datetime | None
    list_id: uuid.UUID
    assignee_id: uuid.UUID | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class CardDetailResponse(CardResponse):
    """Resposta expandida com histórico — usada no GET /cards/{id}."""
    history: list[CardHistoryResponse] = []