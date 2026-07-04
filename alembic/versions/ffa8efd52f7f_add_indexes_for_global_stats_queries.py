"""Add indexes for global stats queries

Revision ID: ffa8efd52f7f
Revises: a1b2c3d4e5f6
Create Date: 2026-07-04 16:11:30.845193

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ffa8efd52f7f'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Missing indexes for global stats queries (IF NOT EXISTS for idempotency)
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_player1_id ON matches(player1_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_partner_id ON matches(partner_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_played_at ON matches(played_at)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_tournament_id ON matches(tournament_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_tournaments_fep_points ON tournaments(fep_points)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_tournaments_fep_points")
    op.execute("DROP INDEX IF EXISTS ix_matches_tournament_id")
    op.execute("DROP INDEX IF EXISTS ix_matches_played_at")
    op.execute("DROP INDEX IF EXISTS ix_matches_partner_id")
    op.execute("DROP INDEX IF EXISTS ix_matches_player1_id")