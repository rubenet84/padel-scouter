"""Repositorio de usuarios para el panel de administración.

Consultas de LECTURA con agregaciones en una sola SQL (evita N+1):
- listado paginado con contadores por usuario (jugadores/partidos/torneos)
- detalle de un usuario
- estadísticas globales (totales por rol y suspendidos)
- conteo/bloqueo de administradores activos (invariante "último admin")

Solo lectura: las mutaciones (rol/estado) las realiza el router vía ORM +
auditoría, siguiendo el patrón pragmático del proyecto.
"""
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

# Contadores por usuario resueltos con subconsultas agregadas (sin N+1).
_USER_COUNTS = """
    COALESCE(pl.cnt, 0) AS players_count,
    COALESCE(ma.cnt, 0) AS matches_count,
    COALESCE(tn.cnt, 0) AS tournaments_count
"""

_USER_JOINS = """
    LEFT JOIN (
        SELECT owner_id, COUNT(*) AS cnt FROM players
        WHERE is_deleted = false GROUP BY owner_id
    ) pl ON pl.owner_id = u.id
    LEFT JOIN (
        SELECT p.owner_id, COUNT(*) AS cnt FROM matches m
        JOIN players p ON p.id = m.player1_id
        GROUP BY p.owner_id
    ) ma ON ma.owner_id = u.id
    LEFT JOIN (
        SELECT owner_id, COUNT(*) AS cnt FROM tournaments GROUP BY owner_id
    ) tn ON tn.owner_id = u.id
"""

_BASE_SELECT = f"""
    SELECT u.id, u.username, u.email, u.role, u.is_active, u.created_at,
           {_USER_COUNTS}
    FROM users u
    {_USER_JOINS}
"""


def _filters(search: str | None, role: str | None, is_active: bool | None) -> tuple[str, dict]:
    clauses: list[str] = []
    params: dict = {}
    if search:
        clauses.append("(u.username ILIKE :search OR u.email ILIKE :search)")
        params["search"] = f"%{search}%"
    if role:
        clauses.append("u.role = :role")
        params["role"] = role
    if is_active is not None:
        clauses.append("u.is_active = :is_active")
        params["is_active"] = is_active
    return (" AND ".join(clauses) if clauses else "TRUE"), params


def list_users(
    db: Session,
    *,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
    limit: int = 25,
    offset: int = 0,
) -> list:
    """Usuarios paginados con contadores (orden estable: created_at DESC)."""
    where, params = _filters(search, role, is_active)
    params.update({"limit": limit, "offset": offset})
    return db.execute(
        text(f"{_BASE_SELECT} WHERE {where} ORDER BY u.created_at DESC LIMIT :limit OFFSET :offset"),
        params,
    ).fetchall()


def count_users(
    db: Session,
    *,
    search: str | None = None,
    role: str | None = None,
    is_active: bool | None = None,
) -> int:
    """Total de usuarios que cumplen los filtros (para paginación)."""
    where, params = _filters(search, role, is_active)
    return db.execute(text(f"SELECT COUNT(*) FROM users u WHERE {where}"), params).scalar() or 0


def get_user(db: Session, user_id: UUID):
    """Detalle de un usuario (con contadores) o None si no existe."""
    return db.execute(text(f"{_BASE_SELECT} WHERE u.id = :uid"), {"uid": user_id}).first()


def user_stats(db: Session):
    """Totales globales por rol y suspendidos."""
    return db.execute(
        text("""
            SELECT
              COUNT(*) AS total,
              COUNT(*) FILTER (WHERE role = 'admin')      AS admins,
              COUNT(*) FILTER (WHERE role = 'entrenador') AS entrenadores,
              COUNT(*) FILTER (WHERE role = 'jugador')    AS jugadores,
              COUNT(*) FILTER (WHERE is_active = false)   AS suspended
            FROM users
        """)
    ).first()


def count_active_admins(db: Session) -> int:
    """Número de administradores activos (invariante: nunca 0)."""
    return db.execute(
        text("SELECT COUNT(*) FROM users WHERE role = 'admin' AND is_active = true")
    ).scalar() or 0


def lock_active_admins(db: Session) -> None:
    """Bloquea (FOR UPDATE) las filas de admins activos para serializar cambios.

    Se usa dentro de la misma transacción que el cambio de rol/estado para que
    dos operaciones concurrentes no puedan dejar 0 admins activos. No hace commit.
    """
    db.execute(text("SELECT id FROM users WHERE role = 'admin' AND is_active = true FOR UPDATE"))
