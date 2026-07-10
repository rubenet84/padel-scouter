"""Per-player metrics computation — batch metrics from match data.

All per-player metric aggregation across the application
should go through this module.
"""

from collections import defaultdict
from uuid import UUID


def compute_player_match_metrics(
    match_rows: list,
    player_ids: list[UUID],
) -> dict[UUID, dict]:
    """Core match-derived metrics for a batch of players.

    Returns dict[pid -> {wins, losses, matches, win_pct, sets_won, games_won, streak}]
    These are the base metrics derived directly from match history,
    shared by rankings, comparisons, and extended metrics.
    """
    # Group matches by player
    player_matches: dict[UUID, list] = defaultdict(list)
    for m in match_rows:
        for pid in player_ids:
            if m.player1_id == pid or m.partner_id == pid:
                player_matches[pid].append(m)

    result: dict[UUID, dict] = {}
    for pid in player_ids:
        pms = player_matches.get(pid, [])

        wins = sum(1 for m in pms if m.ganado)
        losses = sum(1 for m in pms if not m.ganado)
        total = len(pms)
        win_pct = round(wins / total * 100, 1) if total > 0 else 0.0

        sets_won = 0
        games_won = 0
        for m in pms:
            if not m.resultado:
                continue
            for s in m.resultado.split():
                parts = s.split("-")
                if len(parts) != 2:
                    continue
                try:
                    ps, rs = int(parts[0]), int(parts[1])
                    games_won += ps
                    if ps > rs:
                        sets_won += 1
                except ValueError:
                    continue

        # Best streak: longest winning run
        best_streak = 0
        current = 0
        for m in pms:  # ordered by played_at DESC (most recent first)
            if m.ganado:
                current += 1
                if current > best_streak:
                    best_streak = current
            else:
                current = 0
        streak = best_streak

        result[pid] = {
            "wins": wins,
            "losses": losses,
            "matches": total,
            "win_pct": win_pct,
            "sets_won": sets_won,
            "games_won": games_won,
            "streak": streak,
        }
    return result


def _compute_player_metrics(
    match_rows: list,
    player_ids: list[UUID],
    fep_points: dict[UUID, int],
) -> dict[UUID, dict]:
    """Compute all metrics for a batch of players from their match data."""
    # 1. Base match-derived metrics (wins, losses, sets, games, streak)
    base = compute_player_match_metrics(match_rows, player_ids)

    # 2. Initialize result with defaults for ALL player_ids
    result: dict[UUID, dict] = {}
    for pid in player_ids:
        entry = dict(
            base.get(
                pid,
                {
                    "wins": 0,
                    "losses": 0,
                    "matches": 0,
                    "win_pct": 0.0,
                    "sets_won": 0,
                    "games_won": 0,
                    "streak": 0,
                },
            )
        )
        entry["tournaments_won"] = 0
        entry["finals"] = 0
        entry["semis"] = 0
        result[pid] = entry

    # 3. Enrich with tournament-specific data (lightweight — no resultado parsing)
    for m in match_rows:
        for pid in player_ids:
            if not (m.player1_id == pid or m.partner_id == pid):
                continue
            if m.ganado and m.tournament_id:
                result[pid]["tournaments_won"] += 1
            ronda = (getattr(m, "ronda", None) or "").strip()
            if ronda == "Final":
                result[pid]["finals"] += 1
            elif ronda == "Semifinal":
                result[pid]["semis"] += 1

    for pid in player_ids:
        result[pid]["points"] = fep_points.get(pid, 0)

    return result
