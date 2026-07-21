"""Player repository — data access for player queries."""

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
