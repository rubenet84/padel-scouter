"""Repositorio de jugadores — acceso a datos para consultas de players.

Provee la consulta base de jugadores por propietario, filtrando
automáticamente los eliminados (soft delete), además de utilidades de
conteo y resolución de propietario para la capa de autorización.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def get_players_by_owner(
    db: Session,
    owner_id: UUID,
) -> list:
    """All players for a given owner, ordered by name."""
    return db.execute(
        text("""
            SELECT id, name, category
            FROM players
            WHERE owner_id = :uid
              AND is_deleted = false
            ORDER BY name
        """),
        {"uid": owner_id},
    ).fetchall()


def get_all_players(db: Session) -> list:
    """Todos los jugadores no eliminados, sin filtro de propietario.

    Solo debe usarse cuando el alcance es explícitamente global (admin),
    decidido por access_service — nunca por ausencia de owner_id.
    """
    return db.execute(
        text("""
            SELECT id, name, category
            FROM players
            WHERE is_deleted = false
            ORDER BY name
        """),
    ).fetchall()


def count_players_by_owner(
    db: Session,
    owner_id: UUID,
) -> int:
    """Cuenta los jugadores NO eliminados de un propietario.

    Se usa para comprobar límites por rol. Requiere un owner_id no nulo
    (la capa de servicio lo garantiza fail-closed).
    """
    return db.execute(
        text("""
            SELECT COUNT(*)
            FROM players
            WHERE owner_id = :uid
              AND is_deleted = false
        """),
        {"uid": owner_id},
    ).scalar() or 0


def get_player_owner_id(
    db: Session,
    player_id: UUID,
) -> UUID | None:
    """Devuelve el owner_id de un jugador, o None si no existe.

    No filtra por is_deleted: la comprobación de acceso debe funcionar también
    para jugadores restaurables (soft-deleted).
    """
    row = db.execute(
        text("SELECT owner_id FROM players WHERE id = :pid"),
        {"pid": player_id},
    ).first()
    return row[0] if row else None
