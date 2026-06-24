from datetime import datetime, timezone
from jose import jwt
from app.core.security import (
    hash_password, verify_password,
    create_access_token, create_refresh_token, decode_token,
)
from app.core.config import settings

UTC = timezone.utc


class TestPasswords:

    def test_hash_es_diferente_al_original(self):
        hashed = hash_password("mi_password_123")
        assert hashed != "mi_password_123"

    def test_verificar_password_correcto(self):
        hashed = hash_password("mi_password_123")
        assert verify_password("mi_password_123", hashed) is True

    def test_verificar_password_incorrecto(self):
        hashed = hash_password("mi_password_123")
        assert verify_password("password_malo", hashed) is False

    def test_dos_hashes_del_mismo_password_son_distintos(self):
        h1 = hash_password("mismo_password")
        h2 = hash_password("mismo_password")
        assert h1 != h2  # bcrypt usa salt aleatorio


class TestJWTTokens:

    def test_access_token_contiene_sub(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["sub"] == "user-123"

    def test_access_token_tipo_correcto(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["type"] == "access"

    def test_refresh_token_tipo_correcto(self):
        token = create_refresh_token({"sub": "user-123"})
        payload = decode_token(token)
        assert payload["type"] == "refresh"

    def test_token_tiene_expiracion(self):
        token = create_access_token({"sub": "user-123"})
        payload = decode_token(token)
        assert "exp" in payload

    def test_token_invalido_lanza_error(self):
        from jose import JWTError
        import pytest
        with pytest.raises(JWTError):
            decode_token("token.falso.invalido")

    def test_access_y_refresh_son_distintos(self):
        access = create_access_token({"sub": "user-123"})
        refresh = create_refresh_token({"sub": "user-123"})
        assert access != refresh