"""Global summary — aggregate totals + ranking leader + best win %."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.computed_stats import get_computed_stats
from app.domain.value_objects.queries import get_players_by_owner
from app.schemas.stats import GlobalSummary, PlayerBrief


def get_global_summary(db: Session, user_id: UUID) -> GlobalSummary:
    """Aggregate totals + ranking leader + best win % for a single user."""
    # ── All players owned by this user ───────────────────────────
    players = get_players_by_owner(db, user_id)

    total_players = len(players)

    if total_players == 0:
        return GlobalSummary(
            total_players=0,
            total_matches=0,
            total_tournaments=0,
            total_friendlies=0,
            total_sets=0,
            total_games=0,
            ranking_leader=None,
            best_win_pct=None,
        )

    player_ids = [p.id for p in players]

    # ── All matches for these players ────────────────────────────
    match_rows = db.execute(
        text("""
            SELECT m.tournament_id, m.resultado, m.ganado,
                   m.player1_id
            FROM matches m
            WHERE m.player1_id = ANY(:pids)
               OR m.partner_id = ANY(:pids)
        """),
        {"pids": player_ids},
    ).fetchall()

    total_matches = len(match_rows)

    # ── Tournaments / Friendlies ─────────────────────────────────
    tournament_ids: set[UUID] = set()
    total_friendlies = 0
    for m in match_rows:
        if m.tournament_id:
            tournament_ids.add(m.tournament_id)
        else:
            total_friendlies += 1
    total_tournaments = len(tournament_ids)

    # ── Sets / Games (Python post-process, same as analytics.py) ─
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

    # ── Ranking leader & best win % ──────────────────────────────
    ranking_leader: PlayerBrief | None = None
    best_win_pct: PlayerBrief | None = None
    best_fep = -1
    best_win_rate = -1.0

    for p in players:
        stats = get_computed_stats(db, p.id)

        if stats.fep_points > best_fep:
            best_fep = stats.fep_points
            ranking_leader = PlayerBrief(
                id=p.id,
                name=p.name,
                category=p.category,
                points=stats.fep_points,
                win_pct=stats.win_rate,
            )

        if stats.win_rate > best_win_rate:
            best_win_rate = stats.win_rate
            best_win_pct = PlayerBrief(
                id=p.id,
                name=p.name,
                category=p.category,
                points=stats.fep_points,
                win_pct=stats.win_rate,
            )

    return GlobalSummary(
        total_players=total_players,
        total_matches=total_matches,
        total_tournaments=total_tournaments,
        total_friendlies=total_friendlies,
        total_sets=total_sets,
        total_games=total_games,
        ranking_leader=ranking_leader,
        best_win_pct=best_win_pct,
    )
