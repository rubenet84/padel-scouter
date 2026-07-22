"""
Cliente de caché Redis para respuestas de IA y chatbot.

Implementa un caché key-value con TTL para:
- Respuestas de Gemini en análisis de jugadores (evita gastar cuota).
- Respuestas del chatbot de reglamento (evita llamadas repetidas).

Las claves se generan como hash SHA-256 del contenido serializado,
con un prefijo de versión para invalidar el caché cuando cambia
el prompt de IA.
"""
import json
import hashlib
import redis
from app.core.config import settings


class RedisCache:
    """
    Cache para respuestas de Gemini AI.
    Evita llamadas repetidas a la API (ahorra cuota y tiempo).
    TTL por defecto: 24 horas.
    """

    def __init__(self):
        self._client = redis.from_url(
            settings.redis_url,
            decode_responses=True,
        )

    def _make_key(self, prefix: str, data: dict) -> str:
        """Genera una clave única basada en el contenido serializado.

        Usa SHA-256 truncado a 16 caracteres para mantener las claves
        cortas pero con muy baja probabilidad de colisión.
        """
        raw = json.dumps(data, sort_keys=True)
        hash_val = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_val}"

    VERSION = "v4"  # incrementar cuando cambie el prompt de IA

    def get(self, prefix: str, data: dict) -> dict | None:
        """Recupera un valor del caché. Devuelve None si no existe."""
        key = self._make_key(f"{prefix}:{self.VERSION}", data)
        value = self._client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, prefix: str, data: dict, result: dict, ttl: int = 86400) -> None:
        """Guarda un valor en el caché con TTL en segundos (default: 24h)."""
        key = self._make_key(f"{prefix}:{self.VERSION}", data)
        self._client.setex(key, ttl, json.dumps(result))

    def ping(self) -> bool:
        """Verifica conectividad con Redis."""
        try:
            return self._client.ping()
        except Exception:
            return False


# Instancia singleton para toda la aplicación
redis_cache = RedisCache()