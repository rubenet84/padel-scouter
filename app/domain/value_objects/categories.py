"""Category stats — per-category player aggregation."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy.orm import Session

from app.domain.value_objects.fep import compute_fep_points
from app.domain.value_objects.metrics import _compute_player_metrics
from app.domain.value_objects.queries import (
    build_filters,
    fetch_match_rows,
    get_players_by_owner,
)
from app.schemas.stats import CategoryDetail, TopPlayerEntry


def get_category_details(
    db: Session,
    user_id: UUID,
    category: str | None = None,
    player_limit: int = 5,
    filters: dict | None = None,
) -> list[CategoryDetail]:
    """
    Enhanced per-category stats. If category is None, returns ALL categories.
    For each category: total players, matches, wins, losses, avg win%, avg points.
    If player_limit > 0, include top N players sorted by FEP points.
    Uses a single query for all categories to avoid N+1.
    """
    filters = filters or {}

    players = get_players_by_owner(db, user_id)

    if not players:
        return []

    # Group players by category
    cat_players: dict[str, list] = defaultdict(list)
    for p in players:
        cat_players[p.category].append(p)

    categories_to_process = [category] if category else list(cat_players.keys())
    categories_to_process = [c for c in categories_to_process if c in cat_players]
    if not categories_to_process:
        return []

    all_cat_ids: list[UUID] = []
    for c in categories_to_process:
        all_cat_ids.extend(p.id for p in cat_players[c])

    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=all_cat_ids, **match_filters)

    match_rows = fetch_match_rows(db, where_clause, params)

    # Compute FEP for all relevant players
    fep_points = compute_fep_points(match_rows, all_cat_ids)

    metrics = _compute_player_metrics(match_rows, all_cat_ids, fep_points)
    players_map = {p.id: p for p in players}

    results: list[CategoryDetail] = []
    for cat in categories_to_process:
        cat_ids = [p.id for p in cat_players[cat]]

        cat_total_players = len(cat_ids)
        cat_matches = sum(metrics[pid]["matches"] for pid in cat_ids if pid in metrics)
        cat_wins = sum(metrics[pid]["wins"] for pid in cat_ids if pid in metrics)
        cat_losses = sum(metrics[pid]["losses"] for pid in cat_ids if pid in metrics)
        cat_points = sum(metrics[pid]["points"] for pid in cat_ids if pid in metrics)

        avg_win_pct = round(cat_wins / cat_matches * 100, 1) if cat_matches > 0 else 0.0
        avg_points = round(cat_points / cat_total_players, 1) if cat_total_players > 0 else 0.0

        # Leader (most points)
        leader_pid = max(cat_ids, key=lambda pid: metrics.get(pid, {}).get("points", 0))
        leader_name = players_map[leader_pid].name
        leader_points = metrics.get(leader_pid, {}).get("points", 0)

        # Top N players by points
        top_list: list[TopPlayerEntry] = []
        if player_limit > 0:
            sorted_cat = sorted(
                cat_ids,
                key=lambda pid: metrics.get(pid, {}).get("points", 0),
                reverse=True,
            )
            for pid in sorted_cat[:player_limit]:
                p = players_map[pid]
                top_list.append(
                    TopPlayerEntry(
                        player_id=pid,
                        name=p.name,
                        category=p.category,
                        value=metrics.get(pid, {}).get("points", 0),
                    )
                )

        results.append(
            CategoryDetail(
                category=cat,
                total_players=cat_total_players,
                total_matches=cat_matches,
                total_wins=cat_wins,
                total_losses=cat_losses,
                avg_win_pct=avg_win_pct,
                avg_points=avg_points,
                leader_name=leader_name,
                leader_points=leader_points,
                top_players=top_list,
            )
        )

    return results
