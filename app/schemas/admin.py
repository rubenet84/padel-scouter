"""Schemas Pydantic para el panel de administración (usuarios).

No exponen campos sensibles (p. ej. hashed_password). Reutilizan el patrón de
respuesta paginada del proyecto (total/page/page_size/total_pages).
"""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class AdminUserRow(BaseModel):
    """Fila/entrada administrativa de un usuario (sin datos sensibles)."""
    id: UUID
    username: str
    email: str
    role: str
    is_active: bool
    created_at: datetime
    players_count: int = 0
    matches_count: int = 0
    tournaments_count: int = 0


class AdminUserListResponse(BaseModel):
    """Respuesta paginada del listado de usuarios."""
    items: list[AdminUserRow]
    total: int
    page: int
    page_size: int
    total_pages: int


class AdminUserStats(BaseModel):
    """Totales globales para las tarjetas del panel."""
    total: int
    admins: int
    entrenadores: int
    jugadores: int
    suspended: int


class RoleUpdateRequest(BaseModel):
    """Cambio de rol permitido en el MVP: solo jugador <-> entrenador.

    Un valor fuera de este conjunto (p. ej. "admin") es rechazado con 422.
    """
    role: Literal["jugador", "entrenador"]


class StatusUpdateRequest(BaseModel):
    """Cambio de estado de la cuenta (usa UserModel.is_active)."""
    is_active: bool
