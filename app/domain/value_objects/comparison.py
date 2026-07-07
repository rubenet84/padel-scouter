"""Player comparison — side-by-side stats and head-to-head history."""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session

from app.domain.value_objects.fep import compute_fep_points
from app.domain.value_objects.metrics import _compute_player_metrics
from app.domain.value_objects.queries import build_filters, fetch_match_rows
from app.schemas.stats import ComparisonPlayer, ComparisonResult, H2HMatch, H2HResult


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

    match_rows = fetch_match_rows(db, where_clause, params)

    # Compute FEP points for both players
    fep_both = compute_fep_points(match_rows, [p1_id, p2_id])

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
            cat_rows = fetch_match_rows(db, cat_where, cat_params)

            cat_fep = compute_fep_points(cat_rows, cat_ids)

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
