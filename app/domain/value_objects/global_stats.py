"""Global stats aggregation — single-query totals + per-player computed stats."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.computed_stats import get_computed_stats
from app.domain.value_objects.rounds import best_round_info
from app.schemas.stats import (
    GlobalSummary,
    PlayerBrief,
    PlayerRankRow,
    RankingResponse,
)


def build_filters(
    user_ids: list[UUID] | None = None,
    season: int | None = None,
    competition_type: str | None = None,
    category: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> tuple[str, dict]:
    """
    Build WHERE clause parts and params for reuse across all endpoints.

    Activated in PR #2 — supports season, competition_type, date range.
    Category filtering is handled at the player level (not in match SQL).
    """
    clauses: list[str] = []
    params: dict = {}

    if user_ids:
        clauses.append(
            "(m.player1_id = ANY(:user_ids) OR m.partner_id = ANY(:user_ids))"
        )
        params["user_ids"] = user_ids

    if season is not None:
        clauses.append("EXTRACT(YEAR FROM m.played_at) = :season")
        params["season"] = season

    if competition_type:
        if competition_type == "torneo":
            clauses.append("m.tournament_id IS NOT NULL")
        elif competition_type == "amistoso":
            clauses.append("m.tournament_id IS NULL")

    if date_from:
        clauses.append("m.played_at::date >= :date_from")
        params["date_from"] = date_from

    if date_to:
        clauses.append("m.played_at::date <= :date_to")
        params["date_to"] = date_to

    where_clause = " AND ".join(clauses) if clauses else "TRUE"
    return where_clause, params


def get_global_summary(db: Session, user_id: UUID) -> GlobalSummary:
    """Aggregate totals + ranking leader + best win % for a single user."""
    # ── All players owned by this user ───────────────────────────
    players = db.execute(
        text("""
            SELECT id, name, category
            FROM players
            WHERE owner_id = :uid
            ORDER BY name
        """),
        {"uid": user_id},
    ).fetchall()

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


def get_rankings(
    db: Session,
    user_id: UUID,
    sort_by: str = "points",
    order: str = "desc",
    filters: dict | None = None,
    page: int = 1,
    page_size: int = 50,
) -> RankingResponse:
    """
    Full ranking with FEP points, match stats, sort, filter, and pagination.

    - Points: only tournament matches count (FEP = tournament_points × round_weight)
    - Wins/losses/sets/games/streak: ALL matches (tournament + friendly)
    - Filters: season, competition_type, date_from, date_to affect ALL aggregates
    - Category filter: pre-filters the player list before computing stats
    """
    filters = filters or {}

    # ── 1. All players for this user ──────────────────────────────
    players = db.execute(
        text("""
            SELECT id, name, category
            FROM players
            WHERE owner_id = :uid
            ORDER BY name
        """),
        {"uid": user_id},
    ).fetchall()

    if not players:
        return RankingResponse(
            players=[], total=0, page=page, page_size=page_size, total_pages=0
        )

    # ── 2. Category filter (player-level) ─────────────────────────
    category_filter = filters.get("category")
    if category_filter:
        players = [p for p in players if p.category == category_filter]
        if not players:
            return RankingResponse(
                players=[], total=0, page=page, page_size=page_size, total_pages=0
            )

    player_ids = [p.id for p in players]

    # ── 3. Match-level filter clause ──────────────────────────────
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    # ── 4. Get ALL matches with tournament join (for FEP + stats) ─
    match_rows = db.execute(
        text(f"""
            SELECT m.id, m.player1_id, m.partner_id, m.resultado, m.ganado,
                   m.tournament_id, m.ronda, m.played_at,
                   t.fep_points
            FROM matches m
            LEFT JOIN tournaments t ON m.tournament_id = t.id
            WHERE {where_clause}
            ORDER BY m.played_at DESC
        """),
        params,
    ).fetchall()

    # ── 5. Compute FEP points per player (tournament matches only) ─
    # Group tournament matches by player → tournament
    pt_groups: dict[UUID, dict[UUID, list]] = defaultdict(lambda: defaultdict(list))
    for m in match_rows:
        if not m.tournament_id:
            continue
        for pid in player_ids:
            if m.player1_id == pid or m.partner_id == pid:
                pt_groups[pid][m.tournament_id].append(m)

    fep_points: dict[UUID, int] = {}
    for pid in player_ids:
        total_fep = 0
        for tid, tms in pt_groups.get(pid, {}).items():
            fep_total = tms[0].fep_points or 0
            if fep_total == 0:
                continue
            weight = best_round_info(tms)[2]
            total_fep += int(fep_total * weight)
        fep_points[pid] = total_fep

    # ── 6. Group ALL matches by player ────────────────────────────
    player_matches: dict[UUID, list] = defaultdict(list)
    for m in match_rows:
        for pid in player_ids:
            if m.player1_id == pid or m.partner_id == pid:
                player_matches[pid].append(m)

    # ── 7. Compute per-player stats ───────────────────────────────
    rank_rows: list[dict] = []
    for p in players:
        pid = p.id
        pms = player_matches.get(pid, [])

        wins = sum(1 for m in pms if m.ganado)
        losses = sum(1 for m in pms if not m.ganado)
        total_matches = len(pms)
        win_pct = round(wins / total_matches * 100, 1) if total_matches > 0 else 0.0

        # Sets / Games from resultado parsing
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

        # Streak: consecutive wins/losses from most recent match
        streak = 0
        counting = False
        for m in pms:  # already ordered by played_at DESC
            if not counting:
                counting = True
                streak = 1 if m.ganado else -1
            else:
                same_direction = (streak > 0 and m.ganado) or (
                    streak < 0 and not m.ganado
                )
                if same_direction:
                    streak += 1 if m.ganado else -1
                else:
                    break

        rank_rows.append(
            {
                "position": 0,  # assigned after sort + pagination
                "id": pid,
                "name": p.name,
                "category": p.category,
                "points": fep_points.get(pid, 0),
                "wins": wins,
                "losses": losses,
                "matches": total_matches,
                "win_pct": win_pct,
                "sets_won": sets_won,
                "games_won": games_won,
                "streak": streak,
            }
        )

    # ── 8. Sort ───────────────────────────────────────────────────
    valid_sort_keys = {
        "points", "wins", "win_pct", "matches",
        "sets_won", "games_won", "streak", "name",
    }
    if sort_by not in valid_sort_keys:
        sort_by = "points"

    default_order = {"name": "asc"}
    default_dir = default_order.get(sort_by, "desc")
    reverse = (order or default_dir).lower() == "desc"

    if sort_by == "name":
        rank_rows.sort(key=lambda r: r["name"], reverse=reverse)
    else:
        rank_rows.sort(key=lambda r: r[sort_by], reverse=reverse)

    # ── 9. Paginate ───────────────────────────────────────────────
    total = len(rank_rows)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages)) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rank_rows[start:end]

    # ── 10. Assign positions ──────────────────────────────────────
    for i, row in enumerate(page_rows):
        row["position"] = start + i + 1

    return RankingResponse(
        players=[PlayerRankRow(**r) for r in page_rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )
