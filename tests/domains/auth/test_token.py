import uuid
import pytest
from datetime import timedelta
from jose import jwt, JWTError
from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.config import settings


USER_ID = str(uuid.uuid4())


class TestCreateAccessToken:
    def test_retorna_token_valido(self):
        token = create_access_token(subject=USER_ID)
        payload = decode_token(token)
        assert payload["sub"] == USER_ID
        assert payload["type"] == "access"

    def test_inclui_extra_data(self):
        token = create_access_token(subject=USER_ID, extra_data={"role": "admin"})
        payload = decode_token(token)
        assert payload["role"] == "admin"

    def test_token_expirado_lanca_erro(self):
        # Gera token com expiração no passado
        from datetime import datetime, timezone
        from jose import jwt
        payload = {
            "sub": USER_ID,
            "type": "access",
            "exp": datetime.now(timezone.utc) - timedelta(seconds=1),
        }
        token = jwt.encode(payload, settings.secret_key, algorithm=settings.algorithm)
        with pytest.raises(JWTError):
            decode_token(token)

    def test_token_com_secret_errada_lanca_erro(self):
        token = jwt.encode(
            {"sub": USER_ID, "type": "access"},
            "wrong_secret",
            algorithm=settings.algorithm,
        )
        with pytest.raises(JWTError):
            decode_token(token)


class TestCreateRefreshToken:
    def test_type_e_refresh(self):
        token = create_refresh_token(subject=USER_ID)
        payload = decode_token(token)
        assert payload["type"] == "refresh"
        assert payload["sub"] == USER_ID


class TestPasswordHashing:
    def test_hash_e_diferente_da_senha(self):
        hashed = hash_password("minhasenha")
        assert hashed != "minhasenha"

    def test_verify_senha_correta(self):
        hashed = hash_password("minhasenha")
        assert verify_password("minhasenha", hashed) is True

    def test_verify_senha_errada(self):
        hashed = hash_password("minhasenha")
        assert verify_password("senhaerrada", hashed) is False