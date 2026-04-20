import uuid
from pydantic import BaseModel, EmailStr, Field, field_validator
from datetime import datetime
from .models import UserRole


class UserCreate(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8, max_length=64)
    full_name: str = Field(..., min_length=2, max_length=255)
    registration: str = Field(..., min_length=3, max_length=50)
    sector: str = Field(..., min_length=2, max_length=100)
    position: str = Field(..., min_length=2, max_length=100)
    phone: str | None = Field(None, max_length=20)
    role: UserRole = UserRole.SERVIDOR

    @field_validator("password")
    @classmethod
    def password_strength(cls, v: str) -> str:
        if not any(c.isdigit() for c in v):
            raise ValueError("A senha deve conter ao menos um número")
        if not any(c.isupper() for c in v):
            raise ValueError("A senha deve conter ao menos uma letra maiúscula")
        return v


class UserUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=2, max_length=255)
    sector: str | None = Field(None, min_length=2, max_length=100)
    position: str | None = Field(None, min_length=2, max_length=100)
    phone: str | None = None


class UserAdminUpdate(UserUpdate):
    role: UserRole | None = None
    is_active: bool | None = None
    is_verified: bool | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    role: UserRole
    is_active: bool
    is_verified: bool
    full_name: str
    registration: str
    sector: str
    position: str
    phone: str | None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserSummary(BaseModel):
    id: uuid.UUID
    full_name: str
    email: str
    role: UserRole
    sector: str

    model_config = {"from_attributes": True}