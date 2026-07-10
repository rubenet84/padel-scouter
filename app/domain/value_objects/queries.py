"""Shared SQL queries — reusable data access for domain modules.

Contains the query builders and raw SQL queries that are shared across
multiple domain modules. No business logic — just data access.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


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


def get_players_by_owner(
    db: Session,
    owner_id: UUID,
) -> list:
    """All players for a given owner, ordered by name."""
    return db.execute(
        text("""
            SELECT id, name, category
            FROM players
            WHERE owner_id = :uid
            ORDER BY name
        """),
        {"uid": owner_id},
    ).fetchall()


def fetch_match_rows(
    db: Session,
    where_clause: str,
    params: dict,
) -> list:
    """Match rows with tournament info, filtered by a pre-built WHERE clause.

    This is the core match dataset used by rankings, top players, comparison,
    records, category details, and evolution. It returns the full row objects
    for downstream computation (FEP points, per-player metrics).

    Args:
        db: SQLAlchemy session.
        where_clause: Pre-built WHERE clause (from build_filters or equivalent).
        params: Query parameters matching the WHERE clause.

    Returns:
        List of Row objects with m.* columns + t.fep_points.
    """
    return db.execute(
        text(f"""
            SELECT m.id, m.player1_id, m.partner_id, m.resultado, m.ganado,
                   m.tournament_id, m.ronda, m.played_at,
                   t.fep_points
            FROM matches m
            LEFT JOIN tournaments t ON m.tournament_id = t.id
            WHERE {where_clause}
            ORDER BY m.played_at DESC, m.id DESC
        """),
        params,
    ).fetchall()
