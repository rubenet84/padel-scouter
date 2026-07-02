"""
Endpoint del chatbot de reglamento de pádel.

Incluye caché en Redis para no gastar cuota de la API de Gemini
en preguntas repetidas.
"""
import hashlib
import json
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from app.infrastructure.ai.padel_rules_rag import PadelRulesRAG
from app.infrastructure.cache.redis_client import redis_cache

logger = logging.getLogger(__name__)

router = APIRouter(tags=["chatbot"])

# El índice se carga una vez en memoria al arrancar la app
rag_service = PadelRulesRAG()

CACHE_TTL_SECONDS = 60 * 60 * 24 * 7  # 1 semana

# Compartimos la misma conexión Redis del proyecto
_redis = redis_cache._client


class ChatRequest(BaseModel):
    question: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    answer: str
    cached: bool = False


def _cache_key(question: str) -> str:
    normalized = question.strip().lower()
    digest = hashlib.sha256(normalized.encode("utf-8")).hexdigest()
    return f"padel_chatbot:{digest}"


@router.post("/chatbot/ask", response_model=ChatResponse)
def ask_chatbot(payload: ChatRequest):
    question = payload.question.strip()
    key = _cache_key(question)

    # 1. Intentar servir desde caché
    try:
        cached_value = _redis.get(key)
        if cached_value:
            return ChatResponse(answer=json.loads(cached_value), cached=True)
    except Exception:
        logger.warning("Redis no disponible para el chatbot, se sigue sin caché.")

    # 2. Generar respuesta con RAG + Gemini
    try:
        answer = rag_service.answer(question)
    except RuntimeError as e:
        raise HTTPException(status_code=503, detail=str(e))
    except Exception as e:
        logger.exception("Error generando respuesta del chatbot")
        raise HTTPException(status_code=500, detail="Error al consultar el reglamento.")

    # 3. Guardar en caché (best effort)
    try:
        _redis.setex(key, CACHE_TTL_SECONDS, json.dumps(answer))
    except Exception:
        pass

    return ChatResponse(answer=answer, cached=False)
