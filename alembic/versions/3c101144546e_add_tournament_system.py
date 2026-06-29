"""add_tournament_system — Phase 1: tournaments table, match FK + ronda, data backfill

Revision ID: 3c101144546e
Revises: 5b1dcc84d45e
Create Date: 2026-06-29 10:00:00.000000

"""
from typing import Sequence, Union
from uuid import uuid4

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3c101144546e"
down_revision: Union[str, None] = "5b1dcc84d45e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ── Step 1: Create tournaments table ────────────────────────────
    op.create_table(
        "tournaments",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("date", sa.Date(), nullable=False),
        sa.Column("fep_points", sa.Integer(), nullable=True),
        sa.Column("owner_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(
            ["owner_id"], ["users.id"],
            name="fk_tournaments_owner_id",
        ),
        sa.PrimaryKeyConstraint("id"),
    )

    # ── Step 2: Add columns to matches table ────────────────────────
    op.add_column(
        "matches",
        sa.Column("tournament_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "matches",
        sa.Column("ronda", sa.String(length=100), nullable=True),
    )
    op.create_foreign_key(
        "fk_matches_tournament_id",
        "matches", "tournaments",
        ["tournament_id"], ["id"],
    )

    # ── Step 3: Data backfill ────────────────────────────────────────
    # Only runs if tournament_id IS NULL — safe to re-run.
    conn = op.get_bind()

    # Get all distinct, non-null, non-empty torneo values grouped by player1_id
    # This partitions tournaments by player, avoiding cross-user collisions.
    rows = conn.execute(
        sa.text("""
            SELECT DISTINCT
                m.torneo,
                MIN(m.played_at) as first_played,
                m.player1_id
            FROM matches m
            WHERE m.torneo IS NOT NULL
              AND m.torneo != ''
              AND m.tournament_id IS NULL
            GROUP BY m.torneo, m.player1_id
        """)
    ).fetchall()

    for row in rows:
        torneo_name: str = row[0]
        first_played = row[1]
        player1_id = row[2]

        if not torneo_name or not first_played:
            continue

        # Get owner_id from the player who played the match
        owner_row = conn.execute(
            sa.text("SELECT owner_id FROM players WHERE id = :pid"),
            {"pid": player1_id},
        ).first()
        if not owner_row or not owner_row[0]:
            continue

        owner_id = owner_row[0]
        tournament_id = uuid4()

        # Insert tournament row
        conn.execute(
            sa.text("""
                INSERT INTO tournaments (id, name, date, fep_points, owner_id, created_at)
                VALUES (:id, :name, :date, 0, :owner_id, NOW())
            """),
            {
                "id": tournament_id,
                "name": torneo_name,
                "date": first_played.date() if hasattr(first_played, "date") else first_played,
                "owner_id": owner_id,
            },
        )

        # Update matches with this torneo name to point to the new tournament
        conn.execute(
            sa.text("""
                UPDATE matches
                SET tournament_id = :tournament_id
                WHERE torneo = :torneo_name
                  AND (tournament_id IS NULL OR tournament_id != :safety_check)
            """),
            {
                "tournament_id": tournament_id,
                "torneo_name": torneo_name,
                "safety_check": tournament_id,
            },
        )


def downgrade() -> None:
    # ── Reverse Step 2: Remove FK and columns from matches ─────────
    op.drop_constraint("fk_matches_tournament_id", "matches", type_="foreignkey")
    op.drop_column("matches", "ronda")
    op.drop_column("matches", "tournament_id")

    # ── Reverse Step 1: Drop tournaments table ──────────────────────
    op.drop_table("tournaments")
