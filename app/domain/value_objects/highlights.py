"""Community highlights — records, evolution, and dashboard highlights."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.fep import compute_fep_points
from app.domain.value_objects.metrics import _compute_player_metrics
from app.domain.value_objects.queries import (
    build_filters,
    fetch_match_rows,
    get_players_by_owner,
)
from app.schemas.stats import (
    CommunityHighlights,
    EvolutionEntry,
    PlayerBrief,
    PlayerRecord,
)


# ── PR #4: Community Records ──────────────────────────────────────


def get_records(
    db: Session,
    user_id: UUID,
    filters: dict | None = None,
) -> list[PlayerRecord]:
    """
    Community records — top player for each metric.
    Reuses the same FEP/computation logic from get_top_players.
    Returns one PlayerRecord per metric (the top player for that metric).
    Metrics: points, wins, streak, tournaments_won, finals, semis, sets_won, games_won.
    """
    filters = filters or {}

    players = get_players_by_owner(db, user_id)

    if not players:
        return []

    category_filter = filters.get("category")
    if category_filter:
        players = [p for p in players if p.category == category_filter]
        if not players:
            return []

    player_ids = [p.id for p in players]
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    match_rows = fetch_match_rows(db, where_clause, params)

    # Compute FEP points per player
    fep_points = compute_fep_points(match_rows, player_ids)

    metrics = _compute_player_metrics(match_rows, player_ids, fep_points)
    players_map = {p.id: p for p in players}

    record_config = [
        ("points", "Puntos FEP"),
        ("wins", "Victorias"),
        ("streak", "Racha"),
        ("tournaments_won", "Torneos Ganados"),
        ("finals", "Finales"),
        ("semis", "Semifinales"),
        ("sets_won", "Sets Ganados"),
        ("games_won", "Juegos Ganados"),
    ]

    records: list[PlayerRecord] = []
    for metric_key, metric_label in record_config:
        sorted_pids = sorted(
            metrics.keys(),
            key=lambda pid: metrics[pid][metric_key],
            reverse=True,
        )
        for pid in sorted_pids:
            p = players_map[pid]
            m = metrics[pid]
            if metric_key == "win_pct" and m["matches"] < 1:
                continue
            records.append(
                PlayerRecord(
                    player_id=pid,
                    name=p.name,
                    category=p.category,
                    value=m[metric_key],
                    metric_key=metric_key,
                    metric_label=metric_label,
                )
            )
            break  # only top 1 per metric

    return records


# ── PR #4: Evolution (sparkline-ready) ────────────────────────────


def get_evolution(
    db: Session,
    user_id: UUID,
    filters: dict | None = None,
) -> list[EvolutionEntry]:
    """
    Returns current FEP points per player with empty sparkline array.
    The sparkline is ready for future historical data.
    """
    filters = filters or {}

    players = get_players_by_owner(db, user_id)

    if not players:
        return []

    category_filter = filters.get("category")
    if category_filter:
        players = [p for p in players if p.category == category_filter]
        if not players:
            return []

    player_ids = [p.id for p in players]
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    match_rows = fetch_match_rows(db, where_clause, params)

    # Compute FEP points per player
    fep_points = compute_fep_points(match_rows, player_ids)

    return [
        EvolutionEntry(
            player_id=p.id,
            name=p.name,
            category=p.category,
            current_points=fep_points.get(p.id, 0),
            sparkline=[],
        )
        for p in players
    ]


# ── PR #4: Community Highlights ───────────────────────────────────


def get_community_highlights(
    db: Session,
    user_id: UUID,
    filters: dict | None = None,
) -> CommunityHighlights:
    """
    Community dashboard highlights:
    - Most points: player with highest FEP points
    - Best form: player with highest win % (min 1 match)
    - Best pair: pair with highest win % (min 2 matches together)
    - Most active: player with most matches played
    """
    filters = filters or {}

    players = get_players_by_owner(db, user_id)

    if not players:
        return CommunityHighlights()

    player_ids = [p.id for p in players]
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    match_rows = db.execute(
        text(f"""
            SELECT m.id, m.player1_id, m.partner_id, m.player2_id, m.partner_nombre,
                   m.resultado, m.ganado, m.tournament_id, m.ronda, m.played_at,
                   t.fep_points
            FROM matches m
            LEFT JOIN tournaments t ON m.tournament_id = t.id
            WHERE {where_clause}
            ORDER BY m.played_at DESC
        """),
        params,
    ).fetchall()

    # Compute FEP points
    fep_points = compute_fep_points(match_rows, player_ids)

    metrics = _compute_player_metrics(match_rows, player_ids, fep_points)
    players_map = {p.id: p for p in players}

    # ── Most points ──────────────────────────────────────────
    most_points_pid: UUID | None = None
    most_points_val = -1
    for pid in player_ids:
        pts = fep_points.get(pid, 0)
        if pts > most_points_val:
            most_points_val = pts
            most_points_pid = pid

    most_points: PlayerBrief | None = None
    if most_points_pid and most_points_val > 0:
        p = players_map[most_points_pid]
        most_points = PlayerBrief(
            id=most_points_pid,
            name=p.name,
            category=p.category,
            points=most_points_val,
            win_pct=metrics.get(most_points_pid, {}).get("win_pct", 0.0),
        )

    # ── Best form (highest win %, min 1 match) ───────────────
    best_form_pid: UUID | None = None
    best_form_val = -1.0
    for pid in player_ids:
        m = metrics.get(pid, {})
        if m.get("matches", 0) >= 1 and m.get("win_pct", 0) > best_form_val:
            best_form_val = m["win_pct"]
            best_form_pid = pid

    best_form: PlayerBrief | None = None
    if best_form_pid:
        p = players_map[best_form_pid]
        best_form = PlayerBrief(
            id=best_form_pid,
            name=p.name,
            category=p.category,
            points=fep_points.get(best_form_pid, 0),
            win_pct=best_form_val,
        )

    # ── Best pair (highest win %, min 2 matches together) ────
    pair_stats: dict[frozenset, dict] = {}
    for m in match_rows:
        p1 = m.player1_id
        partner = m.partner_id
        if not partner:
            continue
        if p1 not in players_map or partner not in players_map:
            continue
        pair_key = frozenset([p1, partner])
        if pair_key not in pair_stats:
            pair_stats[pair_key] = {"wins": 0, "total": 0, "members": [p1, partner]}
        pair_stats[pair_key]["total"] += 1
        if m.ganado:
            pair_stats[pair_key]["wins"] += 1

    best_pair: dict | None = None
    best_pair_win_pct = -1.0
    for key, st in pair_stats.items():
        if st["total"] < 2:
            continue
        wp = st["wins"] / st["total"] * 100
        if wp > best_pair_win_pct:
            best_pair_win_pct = wp
            members = list(key)
            best_pair = {
                "player1_id": str(members[0]),
                "player2_id": str(members[1]),
                "player1_name": players_map[members[0]].name,
                "player2_name": players_map[members[1]].name,
                "win_pct": round(wp, 1),
                "matches": st["total"],
            }

    # ── Most active (most matches) ───────────────────────────
    most_active_pid: UUID | None = None
    most_active_val = -1
    for pid in player_ids:
        mt = metrics.get(pid, {}).get("matches", 0)
        if mt > most_active_val:
            most_active_val = mt
            most_active_pid = pid

    most_active: PlayerBrief | None = None
    if most_active_pid and most_active_val > 0:
        p = players_map[most_active_pid]
        most_active = PlayerBrief(
            id=most_active_pid,
            name=p.name,
            category=p.category,
            points=fep_points.get(most_active_pid, 0),
            win_pct=metrics.get(most_active_pid, {}).get("win_pct", 0.0),
        )

    return CommunityHighlights(
        most_points=most_points,
        best_form=best_form,
        best_pair=best_pair,
        most_active=most_active,
    )
