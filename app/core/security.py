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
    """
    Decodifica y valida un JWT.
    Lanza JWTError si es inválido o expirado.
    """
    return jwt.decode(
        token,
        settings.secret_key.get_secret_value(),
        algorithms=[settings.algorithm],
    )

def create_reset_token(email: str) -> str:
    """
    OWASP A07 — token de reset de contraseña.
    Firmado con JWT, expira en 15 minutos, tipo 'reset'.
    """
    from datetime import datetime, timedelta, timezone
    from app.core.config import settings
    expire = datetime.now(timezone.utc) + timedelta(
        minutes=settings.reset_token_expire_minutes
    )
    return jwt.encode(
        {"sub": email, "exp": expire, "type": "reset"},
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def verify_reset_token(token: str) -> str | None:
    """
    Verifica el token de reset y devuelve el email si es válido.
    Devuelve None si expiró o es inválido.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ── Download tokens (PDF export, short-lived) ──────────────────

DOWNLOAD_TOKEN_EXPIRE_MINUTES = 5


def create_download_token(user_id: str, player_id: str) -> str:
    """Token de un solo uso para descargar PDF sin exponer JWT en URL."""
    expire = datetime.now(UTC) + timedelta(minutes=DOWNLOAD_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "player_id": player_id, "exp": expire, "type": "download"},
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def decode_download_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un download token. Lanza JWTError si expiró."""
    payload = decode_token(token)
    if payload.get("type") != "download":
        raise JWTError("Token type mismatch")
    return payload