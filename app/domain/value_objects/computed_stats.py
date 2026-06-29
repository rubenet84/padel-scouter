from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


# ── Puntos FEP por ronda (% del total del torneo) ────────────────
ROUND_WEIGHTS: dict[str, float] = {
    "Fase de grupos": 0.0,
    "32avos":        0.1780,
    "16avos":        0.2373,
    "Octavos":       0.3164,
    "Cuartos":       0.4218,
    "Semifinal":     0.5625,
    "Final":         0.75,
}

# Orden jerárquico de rondas (de menor a mayor)
ROUND_ORDER: list[str] = [
    "Fase de grupos", "32avos", "16avos", "Octavos",
    "Cuartos", "Semifinal", "Final",
]


@dataclass
class ComputedStats:
    """Competitive stats computed from match + tournament data."""

    torneos: int = 0
    win_rate: float = 0.0  # 0–100 percentage
    fep_points: int = 0


def _best_round_weight(matches: list) -> float:
    """
    Calcula los puntos según la mejor ronda del jugador en el torneo.

    1. Busca la ronda más alta donde haya una VICTORIA.
    2. Si ganó la Final → campeón (100%).
    3. Si no hay ninguna victoria → usa la ronda más alta ALCANZADA.
    """
    win_idx = -1
    reach_idx = -1

    for m in matches:
        ronda = m.ronda or ""
        if ronda in ROUND_ORDER:
            idx = ROUND_ORDER.index(ronda)
            if idx > reach_idx:
                reach_idx = idx
            if m.ganado and idx > win_idx:
                win_idx = idx

    if win_idx >= 0 and ROUND_ORDER[win_idx] == "Final":
        return 1.0  # 100% — campeón

    if win_idx >= 0:
        return ROUND_WEIGHTS.get(ROUND_ORDER[win_idx], 0.0)

    # Sin victorias: usar la ronda más alta alcanzada
    if reach_idx >= 0:
        return ROUND_WEIGHTS.get(ROUND_ORDER[reach_idx], 0.0)

    return 0.0


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
            WHERE m.player1_id = :player_id
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
            WHERE m.player1_id = :player_id AND m.tournament_id IS NOT NULL
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
        weight = _best_round_weight(tour_matches)
        total_fep += int(fep_total * weight)

    return ComputedStats(
        torneos=torneos,
        win_rate=win_rate,
        fep_points=total_fep,
    )
