import uuid
from datetime import datetime
from pydantic import BaseModel, Field
from app.domain.boards.models import BoardRole


class BoardCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class BoardUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=100)
    description: str | None = Field(None, max_length=500)


class BoardResponse(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    owner_id: uuid.UUID
    created_at: datetime
    updated_at: datetime

class BoardMemberCreate(BaseModel):
    user_id: uuid.UUID
    role: BoardRole = BoardRole.MEMBER


class BoardMemberUpdate(BaseModel):
    role: BoardRole


class BoardMemberResponse(BaseModel):
    id: uuid.UUID
    board_id: uuid.UUID
    user_id: uuid.UUID
    role: BoardRole
    added_at: datetime

model_config = {"from_attributes": True}