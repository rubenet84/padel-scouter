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
        """Genera una clave única basada en el contenido."""
        raw = json.dumps(data, sort_keys=True)
        hash_val = hashlib.sha256(raw.encode()).hexdigest()[:16]
        return f"{prefix}:{hash_val}"

    VERSION = "v2"  # incrementar cuando cambie el prompt de IA

    def get(self, prefix: str, data: dict) -> dict | None:
        key = self._make_key(f"{prefix}:{self.VERSION}", data)
        value = self._client.get(key)
        if value:
            return json.loads(value)
        return None

    def set(self, prefix: str, data: dict, result: dict, ttl: int = 86400) -> None:
        key = self._make_key(f"{prefix}:{self.VERSION}", data)
        self._client.setex(key, ttl, json.dumps(result))

    def ping(self) -> bool:
        try:
            return self._client.ping()
        except Exception:
            return False


redis_cache = RedisCache()