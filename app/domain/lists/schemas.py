import uuid
from datetime import datetime
from pydantic import BaseModel, Field


class ListCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    position: int = Field(0, ge=0)


class ListUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    position: int | None = Field(None, ge=0)


class ListResponse(BaseModel):
    id: uuid.UUID
    name: str
    position: int
    board_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}