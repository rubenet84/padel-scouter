"""
Módulo de seguridad: hashing de contraseñas, tokens JWT y tokens de descarga.

Implementa:
- Hashing de contraseñas con bcrypt (12 rondas de salt).
- Tokens JWT de acceso (corta duración) y refresh (larga duración).
- Tokens de reseteo de contraseña (OWASP A07 compliant).
- Tokens de descarga de PDF de un solo uso (evita exponer JWT en URLs).

Todos los tokens usan la misma clave secreta (settings.secret_key) y
algoritmo (HS256) configurados en app.core.config.
"""
from datetime import datetime, timedelta, timezone
from typing import Any
import bcrypt
from jose import JWTError, jwt
from app.core.config import settings

UTC = timezone.utc


# ── Passwords ─────────────────────────────────────────────────

def hash_password(password: str) -> str:
    """Hashea una contraseña en texto plano usando bcrypt con 12 rondas de salt.

    El resultado es una cadena que incluye el salt y el hash, lista para
    almacenar en base de datos. No es necesario almacenar el salt por separado.
    """
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    """Verifica que una contraseña en texto plano coincida con su hash bcrypt.

    Comparación en tiempo constante para prevenir timing attacks.
    """
    return bcrypt.checkpw(
        plain.encode("utf-8"),
        hashed.encode("utf-8")
    )


# ── JWT Tokens ────────────────────────────────────────────────

def create_access_token(data: dict[str, Any]) -> str:
    """Crea un token JWT de acceso con claims: sub, role, exp, type='access'.

    Expira según settings.access_token_expire_minutes (por defecto 30 min).
    Se usa para autenticar requests a endpoints protegidos.
    """
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
    """Crea un token JWT de refresco con claims: sub, exp, type='refresh'.

    Expira según settings.refresh_token_expire_days (por defecto 7 días).
    Se usa para obtener nuevos access tokens sin volver a pedir credenciales.
    """
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

    El token se envía por email al usuario. En el endpoint de reset,
    se verifica con verify_reset_token() antes de permitir el cambio.
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
    Devuelve None si expiró, no es tipo 'reset', o es inválido.
    """
    try:
        payload = decode_token(token)
        if payload.get("type") != "reset":
            return None
        return payload.get("sub")
    except JWTError:
        return None


# ── Download tokens (PDF export, short-lived) ──────────────────

# Duración de los tokens de descarga: 5 minutos — suficiente para
# que el frontend haga la request al endpoint de PDF inmediatamente
# después de obtener el token.
DOWNLOAD_TOKEN_EXPIRE_MINUTES = 5


def create_download_token(user_id: str, player_id: str) -> str:
    """Token de un solo uso para descargar PDF sin exponer JWT en URL.

    Args:
        user_id: ID del usuario autenticado.
        player_id: ID del jugador cuyo informe se va a descargar.

    Returns:
        Token JWT firmado con tipo 'download' que expira en 5 minutos.
    """
    expire = datetime.now(UTC) + timedelta(minutes=DOWNLOAD_TOKEN_EXPIRE_MINUTES)
    return jwt.encode(
        {"sub": user_id, "player_id": player_id, "exp": expire, "type": "download"},
        settings.secret_key.get_secret_value(),
        algorithm=settings.algorithm,
    )


def decode_download_token(token: str) -> dict[str, Any]:
    """Decodifica y valida un download token. Lanza JWTError si expiró.

    Además de la validación de firma y expiración, verifica que el tipo
    sea 'download' para evitar reutilización de otros tipos de token.
    """
    payload = decode_token(token)
    if payload.get("type") != "download":
        raise JWTError("Token type mismatch")
    return payload