"""Global stats aggregation — single-query totals + per-player computed stats."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.computed_stats import get_computed_stats
from app.domain.value_objects.rounds import best_round_info
from app.schemas.stats import (
    CategoryDetail,
    CommunityHighlights,
    ComparisonPlayer,
    ComparisonResult,
    EvolutionEntry,
    GlobalSummary,
    H2HMatch,
    H2HResult,
    PlayerBrief,
    PlayerRankRow,
    PlayerRecord,
    RankingResponse,
    TopLists,
    TopPlayerEntry,
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


# ── Helper: per-player metrics ────────────────────────────────────


def _compute_player_metrics(
    match_rows: list,
    player_ids: list[UUID],
    fep_points: dict[UUID, int],
) -> dict[UUID, dict]:
    """Compute all metrics for a batch of players from their match data."""
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
        tournament_won = 0
        finals = 0
        semis = 0

        for m in pms:
            if m.ganado and m.tournament_id:
                tournament_won += 1
            ronda = (getattr(m, "ronda", None) or "").strip()
            if ronda == "Final":
                finals += 1
            elif ronda == "Semifinal":
                semis += 1

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

        # Streak
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

        result[pid] = {
            "wins": wins,
            "losses": losses,
            "matches": total,
            "win_pct": win_pct,
            "sets_won": sets_won,
            "games_won": games_won,
            "tournaments_won": tournament_won,
            "finals": finals,
            "semis": semis,
            "streak": streak,
            "points": fep_points.get(pid, 0),
        }
    return result


# ── PR #3: Top Jugadores (10 rankings) ────────────────────────────


def get_top_players(
    db: Session,
    user_id: UUID,
    filters: dict | None = None,
) -> TopLists:
    """
    Returns 10 independent top-5 lists of players by various metrics.
    All lists respect global filters via build_filters().
    """
    filters = filters or {}

    # 1. Get all players for this user
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
        return TopLists()

    category_filter = filters.get("category")
    if category_filter:
        players = [p for p in players if p.category == category_filter]
        if not players:
            return TopLists()

    player_ids = [p.id for p in players]

    # 2. Build match filter clause
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(user_ids=player_ids, **match_filters)

    # 3. Fetch all matches with tournament info
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

    # 4. Compute FEP points per player (same as get_rankings)
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

    # 5. Compute all metrics per player
    metrics = _compute_player_metrics(match_rows, player_ids, fep_points)

    players_map = {p.id: p for p in players}

    def top_n(metric_key: str, n: int = 5) -> list[TopPlayerEntry]:
        """Get top n players by a given metric key."""
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
                continue  # min 1 match for win %
            result.append(
                TopPlayerEntry(
                    player_id=pid,
                    name=p.name,
                    category=p.category,
                    value=m[metric_key],
                )
            )
        return result

    return TopLists(
        top_points=top_n("points"),
        top_wins=top_n("wins"),
        top_win_pct=top_n("win_pct"),
        top_matches=top_n("matches"),
        top_tournaments_won=top_n("tournaments_won"),
        top_finals=top_n("finals"),
        top_semis=top_n("semis"),
        top_sets_won=top_n("sets_won"),
        top_games_won=top_n("games_won"),
        top_streak=top_n("streak"),
    )


# ── PR #3: Comparador ─────────────────────────────────────────────


def get_comparison(
    db: Session,
    user_id: UUID,
    p1_id: UUID,
    p2_id: UUID,
    filters: dict | None = None,
) -> ComparisonResult:
    """
    Side-by-side stats comparison for two players.
    Returns positions and point difference if same category.
    """
    filters = filters or {}

    # 1. Validate both players exist and belong to user
    players = db.execute(
        text("""
            SELECT id, name, category, avatar_url
            FROM players
            WHERE id = ANY(:pids) AND owner_id = :uid
        """),
        {"pids": [p1_id, p2_id], "uid": user_id},
    ).fetchall()

    if len(players) != 2:
        found_ids = {p.id for p in players}
        missing = [str(pid) for pid in [p1_id, p2_id] if pid not in found_ids]
        raise ValueError(f"Players not found: {', '.join(missing)}")

    p_map = {p.id: p for p in players}
    p1 = p_map[p1_id]
    p2 = p_map[p2_id]
    same_category = p1.category == p2.category

    # 2. Compute per-player stats
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}
    where_clause, params = build_filters(
        user_ids=[p1_id, p2_id], **match_filters
    )

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

    # Compute FEP points for both players
    pt_groups: dict[UUID, dict[UUID, list]] = defaultdict(lambda: defaultdict(list))
    for m in match_rows:
        if not m.tournament_id:
            continue
        for pid in [p1_id, p2_id]:
            if m.player1_id == pid or m.partner_id == pid:
                pt_groups[pid][m.tournament_id].append(m)

    fep_both: dict[UUID, int] = {}
    for pid in [p1_id, p2_id]:
        total_fep = 0
        for tid, tms in pt_groups.get(pid, {}).items():
            fep_total = tms[0].fep_points or 0
            if fep_total == 0:
                continue
            weight = best_round_info(tms)[2]
            total_fep += int(fep_total * weight)
        fep_both[pid] = total_fep

    metrics = _compute_player_metrics(match_rows, [p1_id, p2_id], fep_both)
    m1 = metrics.get(p1_id, {})
    m2 = metrics.get(p2_id, {})

    # 3. Find ranking positions (if same category)
    position_a = None
    position_b = None
    point_difference = None
    notice = None

    if same_category:
        # Get all players in that category with their FEP points
        cat_players = db.execute(
            text("""
                SELECT id
                FROM players
                WHERE owner_id = :uid AND category = :cat
            """),
            {"uid": user_id, "cat": p1.category},
        ).fetchall()

        if len(cat_players) > 1:
            cat_ids = [p.id for p in cat_players]

            # Get matches for category players
            cat_where, cat_params = build_filters(
                user_ids=cat_ids, **match_filters
            )
            cat_rows = db.execute(
                text(f"""
                    SELECT m.id, m.player1_id, m.partner_id, m.resultado, m.ganado,
                           m.tournament_id, m.ronda, m.played_at,
                           t.fep_points
                    FROM matches m
                    LEFT JOIN tournaments t ON m.tournament_id = t.id
                    WHERE {cat_where}
                    ORDER BY m.played_at DESC
                """),
                cat_params,
            ).fetchall()

            cat_pt_groups: dict[UUID, dict[UUID, list]] = defaultdict(
                lambda: defaultdict(list)
            )
            for m in cat_rows:
                if not m.tournament_id:
                    continue
                for pid in cat_ids:
                    if m.player1_id == pid or m.partner_id == pid:
                        cat_pt_groups[pid][m.tournament_id].append(m)

            cat_fep: dict[UUID, int] = {}
            for pid in cat_ids:
                total_fep = 0
                for tid, tms in cat_pt_groups.get(pid, {}).items():
                    fep_total = tms[0].fep_points or 0
                    if fep_total == 0:
                        continue
                    weight = best_round_info(tms)[2]
                    total_fep += int(fep_total * weight)
                cat_fep[pid] = total_fep

            sorted_cat = sorted(cat_ids, key=lambda pid: cat_fep.get(pid, 0), reverse=True)
            for i, pid in enumerate(sorted_cat):
                if pid == p1_id:
                    position_a = i + 1
                if pid == p2_id:
                    position_b = i + 1

            if position_a and position_b:
                point_difference = abs(
                    cat_fep.get(p1_id, 0) - cat_fep.get(p2_id, 0)
                )
    else:
        notice = "Distinta categoría — los puntos no son directamente comparables"

    return ComparisonResult(
        player_a=ComparisonPlayer(
            id=p1_id,
            name=p1.name,
            category=p1.category,
            avatar=p1.avatar_url,
            position=position_a,
            points=fep_both.get(p1_id, 0),
            matches=m1.get("matches", 0),
            wins=m1.get("wins", 0),
            losses=m1.get("losses", 0),
            win_pct=m1.get("win_pct", 0.0),
            sets_won=m1.get("sets_won", 0),
            games_won=m1.get("games_won", 0),
            streak=m1.get("streak", 0),
        ),
        player_b=ComparisonPlayer(
            id=p2_id,
            name=p2.name,
            category=p2.category,
            avatar=p2.avatar_url,
            position=position_b,
            points=fep_both.get(p2_id, 0),
            matches=m2.get("matches", 0),
            wins=m2.get("wins", 0),
            losses=m2.get("losses", 0),
            win_pct=m2.get("win_pct", 0.0),
            sets_won=m2.get("sets_won", 0),
            games_won=m2.get("games_won", 0),
            streak=m2.get("streak", 0),
        ),
        same_category=same_category,
        category_name=p1.category if same_category else None,
        point_difference=point_difference,
        notice=notice,
    )


# ── PR #3: Historial H2H ──────────────────────────────────────────


def get_h2h(
    db: Session,
    user_id: UUID,
    p1_id: UUID,
    p2_id: UUID,
    filters: dict | None = None,
) -> H2HResult:
    """
    Head-to-head history between two players.
    Two players face each other when one is player1/partner
    and the other is player2 (opponent).
    """
    filters = filters or {}

    # 1. Validate both players exist and belong to user
    players = db.execute(
        text("""
            SELECT id, name
            FROM players
            WHERE id = ANY(:pids) AND owner_id = :uid
        """),
        {"pids": [p1_id, p2_id], "uid": user_id},
    ).fetchall()

    if len(players) != 2:
        found_ids = {p.id for p in players}
        missing = [str(pid) for pid in [p1_id, p2_id] if pid not in found_ids]
        raise ValueError(f"Players not found: {', '.join(missing)}")

    p_map_name = {p.id: p.name for p in players}

    # 2. Build H2H filter: matches where p1 and p2 faced each other
    #    p1 on player1/partner side AND p2 on player2 side, OR vice versa
    match_filter_keys = {"season", "competition_type", "date_from", "date_to"}
    match_filters = {k: v for k, v in filters.items() if k in match_filter_keys}

    # H2H doesn't use user_ids in build_filters — we build custom where
    base_clauses: list[str] = []
    base_params: dict = {}

    if match_filters.get("season") is not None:
        base_clauses.append("EXTRACT(YEAR FROM m.played_at) = :season")
        base_params["season"] = match_filters["season"]

    if match_filters.get("competition_type"):
        if match_filters["competition_type"] == "torneo":
            base_clauses.append("m.tournament_id IS NOT NULL")
        elif match_filters["competition_type"] == "amistoso":
            base_clauses.append("m.tournament_id IS NULL")

    if match_filters.get("date_from"):
        base_clauses.append("m.played_at::date >= :date_from")
        base_params["date_from"] = match_filters["date_from"]

    if match_filters.get("date_to"):
        base_clauses.append("m.played_at::date <= :date_to")
        base_params["date_to"] = match_filters["date_to"]

    # H2H condition: p1 and p2 faced each other
    h2h_condition = """
        (
            (m.player1_id = :p1_id OR m.partner_id = :p1_id)
            AND m.player2_id = :p2_id
        )
        OR
        (
            (m.player1_id = :p2_id OR m.partner_id = :p2_id)
            AND m.player2_id = :p1_id
        )
    """
    base_params["p1_id"] = p1_id
    base_params["p2_id"] = p2_id

    all_clauses = [h2h_condition] + base_clauses
    final_where = " AND ".join(all_clauses)
    final_params = base_params

    h2h_matches = db.execute(
        text(f"""
            SELECT m.id, m.player1_id, m.partner_id, m.player2_id,
                   m.resultado, m.ganado, m.winner_id, m.played_at,
                   m.ronda, m.tournament_id
            FROM matches m
            WHERE {final_where}
            ORDER BY m.played_at DESC
        """),
        final_params,
    ).fetchall()

    total = len(h2h_matches)
    if total == 0:
        return H2HResult(
            player_a_id=p1_id,
            player_b_id=p2_id,
            total_matches=0,
            wins_a=0,
            wins_b=0,
            sets_a=0,
            sets_b=0,
            games_a=0,
            games_b=0,
            last_match=None,
            history=[],
        )

    wins_a = 0
    wins_b = 0
    sets_a = 0
    sets_b = 0
    games_a = 0
    games_b = 0
    history: list[H2HMatch] = []
    last_match: H2HMatch | None = None

    for m in h2h_matches:
        # Determine which player is "p1" (side A) in this match
        p1_is_player1 = m.player1_id == p1_id or m.partner_id == p1_id

        # Parse resultado for sets/games
        m_sets_a = 0
        m_sets_b = 0
        m_games_a = 0
        m_games_b = 0
        if m.resultado:
            for s in m.resultado.split():
                parts = s.split("-")
                if len(parts) == 2:
                    try:
                        ps, rs = int(parts[0]), int(parts[1])
                        if p1_is_player1:
                            m_games_a += ps
                            m_games_b += rs
                            if ps > rs:
                                m_sets_a += 1
                            else:
                                m_sets_b += 1
                        else:
                            m_games_a += rs
                            m_games_b += ps
                            if rs > ps:
                                m_sets_a += 1
                            else:
                                m_sets_b += 1
                    except ValueError:
                        pass

        sets_a += m_sets_a
        sets_b += m_sets_b
        games_a += m_games_a
        games_b += m_games_b

        # Determine winner
        winner_id = m.winner_id
        winner_name = p_map_name.get(winner_id) if winner_id else None

        if winner_id == p1_id:
            wins_a += 1
        elif winner_id == p2_id:
            wins_b += 1
        else:
            # Fallback: use ganado field
            if p1_is_player1:
                if m.ganado:
                    wins_a += 1
                    winner_id = p1_id
                    winner_name = p_map_name.get(p1_id)
                else:
                    wins_b += 1
                    winner_id = p2_id
                    winner_name = p_map_name.get(p2_id)
            else:
                if m.ganado:
                    wins_b += 1
                    winner_id = p2_id
                    winner_name = p_map_name.get(p2_id)
                else:
                    wins_a += 1
                    winner_id = p1_id
                    winner_name = p_map_name.get(p1_id)

        h2h_entry = H2HMatch(
            date=str(m.played_at.date()) if m.played_at else None,
            winner_id=winner_id,
            winner_name=winner_name,
            sets_p1=m_sets_a,
            sets_p2=m_sets_b,
            games_p1=m_games_a,
            games_p2=m_games_b,
            resultado=m.resultado,
        )
        history.append(h2h_entry)

    if history:
        last_match = history[0]

    return H2HResult(
        player_a_id=p1_id,
        player_b_id=p2_id,
        total_matches=total,
        wins_a=wins_a,
        wins_b=wins_b,
        sets_a=sets_a,
        sets_b=sets_b,
        games_a=games_a,
        games_b=games_b,
        last_match=last_match,
        history=history,
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

    # Compute FEP points per player
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


# ── PR #4: Category Details ───────────────────────────────────────


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

    # Compute FEP for all relevant players
    pt_groups: dict[UUID, dict[UUID, list]] = defaultdict(lambda: defaultdict(list))
    for m in match_rows:
        if not m.tournament_id:
            continue
        for pid in all_cat_ids:
            if m.player1_id == pid or m.partner_id == pid:
                pt_groups[pid][m.tournament_id].append(m)

    fep_points: dict[UUID, int] = {}
    for pid in all_cat_ids:
        total_fep = 0
        for tid, tms in pt_groups.get(pid, {}).items():
            fep_total = tms[0].fep_points or 0
            if fep_total == 0:
                continue
            weight = best_round_info(tms)[2]
            total_fep += int(fep_total * weight)
        fep_points[pid] = total_fep

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

    # Compute FEP points per player
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
