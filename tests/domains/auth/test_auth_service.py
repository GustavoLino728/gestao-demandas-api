import uuid
import pytest
from unittest.mock import AsyncMock, patch
from app.domain.auth.service import AuthService
from app.domain.auth.schemas import LoginRequest, RefreshRequest
from app.core.exceptions import UnauthorizedError
from app.core.security import create_refresh_token, hash_password
from tests.conftest import make_user
from app.domain.users.models import UserRole


@pytest.fixture
def active_user():
    user = make_user(role=UserRole.SERVIDOR)
    user.password_hash = hash_password("Senha123!")
    return user


@pytest.fixture
def auth_service(mock_user_repo):
    return AuthService(user_repo=mock_user_repo)


class TestLogin:
    async def test_login_sucesso(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_email.return_value = active_user

        result = await auth_service.login(
            LoginRequest(email="test@example.com", password="Senha123!")
        )

        assert result.access_token
        assert result.refresh_token
        assert result.token_type == "bearer"

    async def test_email_inexistente_retorna_401(self, auth_service, mock_user_repo):
        mock_user_repo.get_by_email.return_value = None

        with pytest.raises(UnauthorizedError) as exc:
            await auth_service.login(
                LoginRequest(email="naoexiste@example.com", password="qualquer")
            )
        assert exc.value.code == 401

    async def test_senha_errada_retorna_401(self, auth_service, mock_user_repo, active_user):
        mock_user_repo.get_by_email.return_value = active_user

        with pytest.raises(UnauthorizedError) as exc:
            await auth_service.login(
                LoginRequest(email="test@example.com", password="senhaerrada")
            )
        assert exc.value.code == 401

    async def test_usuario_inativo_retorna_401(self, auth_service, mock_user_repo):
        inactive_user = make_user(is_active=False)
        inactive_user.password_hash = hash_password("Senha123!")
        mock_user_repo.get_by_email.return_value = inactive_user

        with pytest.raises(UnauthorizedError):
            await auth_service.login(
                LoginRequest(email="test@example.com", password="Senha123!")
            )

    async def test_erro_nao_revela_se_email_existe(self, auth_service, mock_user_repo, active_user):
        """Proteção contra user enumeration — mesmo erro para email e senha inválidos."""
        mock_user_repo.get_by_email.return_value = None
        with pytest.raises(UnauthorizedError) as exc_email:
            await auth_service.login(LoginRequest(email="x@x.com", password="qualquer"))

        mock_user_repo.get_by_email.return_value = active_user
        with pytest.raises(UnauthorizedError) as exc_senha:
            await auth_service.login(LoginRequest(email="test@example.com", password="errada"))

        assert exc_email.value.message == exc_senha.value.message


class TestRefresh:
    async def test_refresh_valido_retorna_novo_access_token(
        self, auth_service, mock_user_repo, active_user
    ):
        mock_user_repo.get_by_id.return_value = active_user
        refresh_token = create_refresh_token(subject=str(active_user.id))

        result = await auth_service.refresh(RefreshRequest(refresh_token=refresh_token))

        assert result.access_token
        assert result.token_type == "bearer"

    async def test_access_token_como_refresh_retorna_401(
        self, auth_service, mock_user_repo, active_user
    ):
        from app.core.security import create_access_token
        mock_user_repo.get_by_id.return_value = active_user
        access_token = create_access_token(subject=str(active_user.id))

        with pytest.raises(UnauthorizedError):
            await auth_service.refresh(RefreshRequest(refresh_token=access_token))

    async def test_token_invalido_retorna_401(self, auth_service):
        with pytest.raises(UnauthorizedError):
            await auth_service.refresh(RefreshRequest(refresh_token="token.invalido.aqui"))

    async def test_usuario_inativo_retorna_401(self, auth_service, mock_user_repo):
        inactive_user = make_user(is_active=False)
        mock_user_repo.get_by_id.return_value = inactive_user
        refresh_token = create_refresh_token(subject=str(inactive_user.id))

        with pytest.raises(UnauthorizedError):
            await auth_service.refresh(RefreshRequest(refresh_token=refresh_token))