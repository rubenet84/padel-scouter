from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.rounds import best_round_info


@dataclass
class ComputedStats:
    """Competitive stats computed from match + tournament data."""

    torneos: int = 0
    win_rate: float = 0.0  # 0–100 percentage
    fep_points: int = 0


def get_computed_stats(db: Session, player_id: UUID) -> ComputedStats:
    """
    Compute competitive stats directly from match + tournament data.

    Puntos FEP: se distribuyen según la mejor ronda alcanzada
    en cada torneo (no se suman planos).
    """
    # ── torneos + win_rate (misma query que antes) ───────────────
    result = db.execute(
        text("""
            SELECT
                COUNT(DISTINCT m.tournament_id) AS torneos,
                CASE
                    WHEN COUNT(*) > 0
                    THEN COUNT(*) FILTER (WHERE m.ganado = true)::float / COUNT(*) * 100
                    ELSE 0.0
                END AS win_rate
            FROM matches m
            WHERE m.player1_id = :player_id OR m.partner_id = :player_id
        """),
        {"player_id": player_id},
    ).first()

    torneos = result.torneos or 0
    win_rate = round(result.win_rate or 0.0, 1)

    # ── Puntos FEP ponderados por ronda ──────────────────────────
    rows = db.execute(
        text("""
            SELECT t.id, t.fep_points, m.ronda, m.ganado
            FROM matches m
            JOIN tournaments t ON m.tournament_id = t.id
            WHERE (m.player1_id = :player_id OR m.partner_id = :player_id) AND m.tournament_id IS NOT NULL
            ORDER BY t.id
        """),
        {"player_id": player_id},
    ).fetchall()

    # Agrupar partidos por torneo
    tour_groups: dict[UUID, list] = defaultdict(list)
    for row in rows:
        tour_groups[row.id].append(row)

    total_fep = 0
    for tour_id, tour_matches in tour_groups.items():
        fep_total = tour_matches[0].fep_points or 0
        if fep_total == 0:
            continue
        weight = best_round_info(tour_matches)[2]  # weight is index 2
        total_fep += int(fep_total * weight)

    return ComputedStats(
        torneos=torneos,
        win_rate=win_rate,
        fep_points=total_fep,
    )
