from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


@dataclass
class ComputedStats:
    """Competitive stats computed from match + tournament data."""

    torneos: int = 0
    win_rate: float = 0.0  # 0–100 percentage
    fep_points: int = 0


def get_computed_stats(db: Session, player_id: UUID) -> ComputedStats:
    """
    Compute competitive stats directly from match + tournament data.

    Returns (0, 0.0, 0) if no matches exist.
    """
    result = db.execute(
        text("""
            SELECT
                COUNT(DISTINCT m.tournament_id) AS torneos,
                CASE
                    WHEN COUNT(*) > 0
                    THEN COUNT(*) FILTER (WHERE m.ganado = true)::float / COUNT(*) * 100
                    ELSE 0.0
                END AS win_rate,
                COALESCE(
                    (SELECT SUM(fep_points) FROM tournaments WHERE id IN (
                        SELECT DISTINCT m2.tournament_id FROM matches m2
                        WHERE m2.player1_id = :player_id AND m2.tournament_id IS NOT NULL
                    )),
                    0
                ) AS fep_points
            FROM matches m
            WHERE m.player1_id = :player_id
        """),
        {"player_id": player_id},
    ).first()

    return ComputedStats(
        torneos=result.torneos or 0,
        win_rate=round(result.win_rate or 0.0, 1),
        fep_points=result.fep_points or 0,
    )
