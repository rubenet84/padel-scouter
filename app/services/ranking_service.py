"""Ranking service — FEP-based ranking and top-player lists."""

from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.value_objects.fep import compute_fep_points
from app.domain.value_objects.metrics import (
    _compute_player_metrics,
    compute_player_match_metrics,
)
from app.infrastructure.repositories.match_repository import build_filters, fetch_match_rows
from app.infrastructure.repositories.player_repository import get_players_by_owner
from app.schemas.stats import (
    PlayerRankRow,
    RankingResponse,
    TopLists,
    TopPlayerEntry,
)


def get_rankings(
    db: Session, user_id: UUID,
    sort_by: str = "points", order: str = "desc",
    filters: dict | None = None,
    page: int = 1, page_size: int = 50,
) -> RankingResponse:
    """Full ranking with FEP points, match stats, sort, filter, and pagination."""
    filters = filters or {}

    players = get_players_by_owner(db, user_id)

    if not players:
        return RankingResponse(players=[], total=0, page=page, page_size=page_size, total_pages=0)

    category_filter = filters.get("category")
    if category_filter:
        players = [p for p in players if p.category == category_filter]
        if not players:
            return RankingResponse(players=[], total=0, page=page, page_size=page_size, total_pages=0)

    player_ids = [p.id for p in players]

    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    match_rows = fetch_match_rows(db, where_clause, params)

    fep_points = compute_fep_points(match_rows, player_ids)
    base_metrics = compute_player_match_metrics(match_rows, player_ids)

    rank_rows: list[dict] = []
    for p in players:
        pid = p.id
        bm = base_metrics.get(pid, {})
        rank_rows.append({
            "position": 0, "id": pid, "name": p.name, "category": p.category,
            "points": fep_points.get(pid, 0),
            "wins": bm.get("wins", 0), "losses": bm.get("losses", 0),
            "matches": bm.get("matches", 0), "win_pct": bm.get("win_pct", 0.0),
            "sets_won": bm.get("sets_won", 0), "games_won": bm.get("games_won", 0),
            "streak": bm.get("streak", 0),
        })

    valid_sort_keys = {"points", "wins", "win_pct", "matches", "sets_won", "games_won", "streak", "name"}
    if sort_by not in valid_sort_keys:
        sort_by = "points"

    default_order = {"name": "asc"}
    default_dir = default_order.get(sort_by, "desc")
    reverse = (order or default_dir).lower() == "desc"

    if sort_by == "name":
        rank_rows.sort(key=lambda r: r["name"], reverse=reverse)
    else:
        rank_rows.sort(key=lambda r: r[sort_by], reverse=reverse)

    total = len(rank_rows)
    total_pages = max(1, (total + page_size - 1) // page_size)
    page = max(1, min(page, total_pages)) if total > 0 else 1
    start = (page - 1) * page_size
    end = start + page_size
    page_rows = rank_rows[start:end]

    for i, row in enumerate(page_rows):
        row["position"] = start + i + 1

    return RankingResponse(
        players=[PlayerRankRow(**r) for r in page_rows],
        total=total, page=page, page_size=page_size, total_pages=total_pages,
    )


def get_top_players(
    db: Session, user_id: UUID, filters: dict | None = None,
) -> TopLists:
    """Returns 10 independent top-5 lists of players by various metrics."""
    filters = filters or {}

    players = get_players_by_owner(db, user_id)

    if not players:
        return TopLists()

    category_filter = filters.get("category")
    if category_filter:
        players = [p for p in players if p.category == category_filter]
        if not players:
            return TopLists()

    player_ids = [p.id for p in players]

    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    match_rows = fetch_match_rows(db, where_clause, params)
    fep_points = compute_fep_points(match_rows, player_ids)
    metrics = _compute_player_metrics(match_rows, player_ids, fep_points)
    players_map = {p.id: p for p in players}

    def top_n(metric_key: str, n: int = 5) -> list[TopPlayerEntry]:
        sorted_pids = sorted(
            metrics.keys(),
            key=lambda pid: metrics[pid][metric_key],
            reverse=True,
        )
        result = []
        for pid in sorted_pids:
            if len(result) >= n:
                break
            p = players_map[pid]
            m = metrics[pid]
            if metric_key == "win_pct" and m["matches"] < 1:
                continue
            result.append(TopPlayerEntry(
                player_id=pid, name=p.name, category=p.category, value=m[metric_key],
            ))
        return result

    return TopLists(
        top_points=top_n("points"), top_wins=top_n("wins"),
        top_win_pct=top_n("win_pct"), top_matches=top_n("matches"),
        top_tournaments_won=top_n("tournaments_won"), top_finals=top_n("finals"),
        top_semis=top_n("semis"), top_sets_won=top_n("sets_won"),
        top_games_won=top_n("games_won"), top_streak=top_n("streak"),
    )
