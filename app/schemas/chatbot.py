"""Schemas Pydantic para el endpoint del chatbot RAG.

Define la request (pregunta del usuario) y la response (respuesta + flag cached).
"""

from pydantic import BaseModel, Field


class ChatRequest(BaseModel):
    """Pregunta del usuario al chatbot. Entre 1 y 500 caracteres."""
    question: str = Field(..., min_length=1, max_length=500)


class ChatResponse(BaseModel):
    """Respuesta del chatbot. Indica si vino de caché Redis."""
    answer: str
    cached: bool = False
