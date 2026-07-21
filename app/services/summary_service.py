"""Summary service — global aggregate totals + ranking leader + best win %."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.computed_stats import ComputedStats
from app.domain.value_objects.rounds import best_round_info
from app.infrastructure.repositories.player_repository import get_players_by_owner
from app.schemas.stats import GlobalSummary, PlayerBrief


def _batch_compute_stats(db: Session, player_ids: list[UUID]) -> dict[UUID, ComputedStats]:
    """Compute torneos + win_rate + fep_points for many players in 2 queries."""
    if not player_ids:
        return {}

    rows = db.execute(
        text("""
            SELECT
                candidates.pid AS player_id,
                COUNT(DISTINCT m.tournament_id) AS torneos,
                CASE
                    WHEN COUNT(*) > 0
                    THEN COUNT(*) FILTER (WHERE m.ganado = true)::float / COUNT(*) * 100
                    ELSE 0.0
                END AS win_rate
            FROM matches m
            JOIN LATERAL (
                VALUES (m.player1_id), (m.partner_id)
            ) AS candidates(pid) ON candidates.pid = ANY(:pids)
            GROUP BY candidates.pid
        """),
        {"pids": player_ids},
    ).fetchall()

    stats_map: dict[UUID, ComputedStats] = {
        row.player_id: ComputedStats(
            torneos=row.torneos or 0,
            win_rate=round(row.win_rate or 0.0, 1),
            fep_points=0,
        )
        for row in rows
    }

    for pid in player_ids:
        if pid not in stats_map:
            stats_map[pid] = ComputedStats(torneos=0, win_rate=0.0, fep_points=0)

    fep_rows = db.execute(
        text("""
            SELECT
                candidates.pid AS player_id,
                t.id AS tournament_id, t.fep_points, m.ronda, m.ganado
            FROM matches m
            JOIN tournaments t ON m.tournament_id = t.id
            JOIN LATERAL (
                VALUES (m.player1_id), (m.partner_id)
            ) AS candidates(pid) ON candidates.pid = ANY(:pids)
            WHERE m.tournament_id IS NOT NULL
            ORDER BY candidates.pid, t.id
        """),
        {"pids": player_ids},
    ).fetchall()

    tour_groups: dict[UUID, dict[UUID, list]] = defaultdict(lambda: defaultdict(list))
    for row in fep_rows:
        tour_groups[row.player_id][row.tournament_id].append(row)

    for pid, tours in tour_groups.items():
        total_fep = 0
        for tour_id, tour_matches in tours.items():
            fep_total = tour_matches[0].fep_points or 0
            if fep_total == 0:
                continue
            weight = best_round_info(tour_matches)[2]
            total_fep += int(fep_total * weight)
        stats_map[pid].fep_points = total_fep

    return stats_map


def get_global_summary(db: Session, user_id: UUID) -> GlobalSummary:
    """Aggregate totals + ranking leader + best win % for a single user."""
    players = get_players_by_owner(db, user_id)

    total_players = len(players)

    if total_players == 0:
        return GlobalSummary(
            total_players=0, total_matches=0, total_tournaments=0,
            total_friendlies=0, total_sets=0, total_games=0,
            ranking_leader=None, best_win_pct=None,
        )

    player_ids = [p.id for p in players]
    stats_map = _batch_compute_stats(db, player_ids)

    match_rows = db.execute(
        text("""
            SELECT m.tournament_id, m.resultado, m.ganado, m.player1_id
            FROM matches m
            WHERE m.player1_id = ANY(:pids) OR m.partner_id = ANY(:pids)
        """),
        {"pids": player_ids},
    ).fetchall()

    total_matches = len(match_rows)

    tournament_ids: set[UUID] = set()
    total_friendlies = 0
    for m in match_rows:
        if m.tournament_id:
            tournament_ids.add(m.tournament_id)
        else:
            total_friendlies += 1
    total_tournaments = len(tournament_ids)

    total_sets = 0
    total_games = 0
    for m in match_rows:
        if not m.resultado:
            continue
        sets_str = m.resultado.split()
        for s in sets_str:
            parts = s.split("-")
            if len(parts) != 2:
                continue
            try:
                ps, rs = int(parts[0]), int(parts[1])
                total_sets += 1
                total_games += ps + rs
            except ValueError:
                continue

    ranking_leader: PlayerBrief | None = None
    best_win_pct: PlayerBrief | None = None
    best_fep = -1
    best_win_rate = -1.0

    for p in players:
        stats = stats_map.get(p.id, ComputedStats())

        if stats.fep_points > best_fep:
            best_fep = stats.fep_points
            ranking_leader = PlayerBrief(
                id=p.id, name=p.name, category=p.category,
                points=stats.fep_points, win_pct=stats.win_rate,
            )

        if stats.win_rate > best_win_rate:
            best_win_rate = stats.win_rate
            best_win_pct = PlayerBrief(
                id=p.id, name=p.name, category=p.category,
                points=stats.fep_points, win_pct=stats.win_rate,
            )

    return GlobalSummary(
        total_players=total_players, total_matches=total_matches,
        total_tournaments=total_tournaments, total_friendlies=total_friendlies,
        total_sets=total_sets, total_games=total_games,
        ranking_leader=ranking_leader, best_win_pct=best_win_pct,
    )
