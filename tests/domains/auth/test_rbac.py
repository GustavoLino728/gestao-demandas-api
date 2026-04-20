import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from app.dependencies import get_current_user_id, require_roles, _extract_payload
from app.core.exceptions import ForbiddenError, credentials_exception
from app.core.security import create_access_token
from app.domain.users.models import UserRole


def make_credentials(token: str) -> HTTPAuthorizationCredentials:
    return HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)


def make_token(role: UserRole, user_id: uuid.UUID | None = None) -> str:
    uid = user_id or uuid.uuid4()
    return create_access_token(
        subject=str(uid),
        extra_data={"role": role.value, "email": "test@test.com"},
    )


class TestExtractPayload:
    async def test_token_valido_retorna_payload(self):
        token = make_token(UserRole.SERVIDOR)
        credentials = make_credentials(token)
        payload = await _extract_payload(credentials)
        assert payload["type"] == "access"
        assert payload["sub"]

    async def test_refresh_token_lanca_401(self):
        from app.core.security import create_refresh_token
        token = create_refresh_token(subject=str(uuid.uuid4()))
        credentials = make_credentials(token)
        with pytest.raises(HTTPException) as exc:
            await _extract_payload(credentials)
        assert exc.value.status_code == 401

    async def test_token_invalido_lanca_401(self):
        credentials = make_credentials("token.invalido")
        with pytest.raises(HTTPException) as exc:
            await _extract_payload(credentials)
        assert exc.value.status_code == 401


class TestGetCurrentUserId:
    async def test_retorna_uuid_do_sub(self):
        user_id = uuid.uuid4()
        token = make_token(UserRole.SERVIDOR, user_id=user_id)
        payload = {"sub": str(user_id), "type": "access"}
        result = await get_current_user_id(payload)
        assert result == user_id


class TestRequireRoles:
    async def test_role_permitido_retorna_user_id(self):
        user_id = uuid.uuid4()
        payload = {"sub": str(user_id), "role": "admin", "type": "access"}
        guard = require_roles(UserRole.ADMIN)
        result = await guard(payload)
        assert result == user_id

    async def test_role_nao_permitido_lanca_403(self):
        payload = {"sub": str(uuid.uuid4()), "role": "servidor", "type": "access"}
        guard = require_roles(UserRole.ADMIN, UserRole.GESTOR)
        with pytest.raises(ForbiddenError) as exc:
            await guard(payload)
        assert exc.value.code == 403

    async def test_multiplos_roles_permitidos(self):
        guard = require_roles(UserRole.ADMIN, UserRole.GESTOR)

        for role in [UserRole.ADMIN, UserRole.GESTOR]:
            payload = {"sub": str(uuid.uuid4()), "role": role.value}
            result = await guard(payload)
            assert result  # não levantou exceção

    async def test_servidor_bloqueado_em_rota_admin(self):
        payload = {"sub": str(uuid.uuid4()), "role": "servidor"}
        guard = require_roles(UserRole.ADMIN)
        with pytest.raises(ForbiddenError):
            await guard(payload)