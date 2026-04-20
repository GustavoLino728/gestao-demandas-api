import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone
from app.domain.users.models import User, UserRole


def make_user(
    role: UserRole = UserRole.SERVIDOR,
    is_active: bool = True,
    id: uuid.UUID | None = None,
) -> User:
    """Factory de User para testes — sem bater no banco."""
    user = User()
    user.id = id or uuid.uuid4()
    user.email = "test@example.com"
    user.password_hash = "$2b$12$KIXQw1234hashedpassword"
    user.full_name = "Test User"
    user.registration = "MAT001"
    user.sector = "TI"
    user.position = "Analista"
    user.phone = "81999999999"
    user.role = role
    user.is_active = is_active
    user.is_verified = True
    user.created_at = datetime.now(timezone.utc)
    user.updated_at = datetime.now(timezone.utc)
    return user


@pytest.fixture
def mock_user_repo():
    repo = AsyncMock()
    repo.get_by_email = AsyncMock(return_value=None)
    repo.get_by_id = AsyncMock(return_value=None)
    return repo