"""FEP points calculation — single source of truth.

All FEP (Federación de Pádel) point calculations across the application
must go through this module.
"""

from collections import defaultdict
from uuid import UUID

from app.domain.value_objects.rounds import best_round_info


def compute_fep_points(
    match_rows: list,
    player_ids: list[UUID],
) -> dict[UUID, int]:
    """
    Compute FEP points per player from tournament match rows.

    For each player, FEP points are calculated by grouping tournament matches
    by tournament, applying the round weight from best_round_info(), and
    summing the weighted points.

    Only tournament matches (m.tournament_id IS NOT NULL) contribute to FEP.
    Friendly matches are excluded from FEP calculation.

    Args:
        match_rows: list of Row objects with at least the attributes
                    tournament_id, fep_points, ronda, ganado, player1_id,
                    and partner_id.
        player_ids: list of player UUIDs to compute FEP for.

    Returns:
        dict mapping each player_id to their total FEP points (int).
    """
    # Group tournament matches by player → tournament
    pt_groups: dict[UUID, dict[UUID, list]] = defaultdict(lambda: defaultdict(list))
    for m in match_rows:
        if not m.tournament_id:
            continue
        for pid in player_ids:
            if m.player1_id == pid or m.partner_id == pid:
                pt_groups[pid][m.tournament_id].append(m)

    result: dict[UUID, int] = {}
    for pid in player_ids:
        total_fep = 0
        for tid, tms in pt_groups.get(pid, {}).items():
            fep_total = tms[0].fep_points or 0
            if fep_total == 0:
                continue
            weight = best_round_info(tms)[2]
            total_fep += int(fep_total * weight)
        result[pid] = total_fep
    return result
