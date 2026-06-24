from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings

UTC = timezone.utc


# ── Passwords ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )


# ── JWT Tokens ────────────────────────────────────────────────

def create_access_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    payload.update({"exp": expire, "type": "access"})
    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def create_refresh_token(data: dict[str, Any]) -> str:
    payload = data.copy()
    expire = datetime.now(UTC) + timedelta(
        days=settings.refresh_token_expire_days
    )
    payload.update({"exp": expire, "type": "refresh"})
    return jwt.encode(
        payload,
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def decode_token(token: str) -> dict[str, Any]:
    return jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )

def decode_token(token: str) -> dict[str, Any]:
    """
    Decodifica y valida un JWT.
    Lanza JWTError si es inválido o expirado.
    """
    return jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )