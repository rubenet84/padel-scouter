"""Add missing match indexes (player2_id, winner_id)

Revision ID: 44a90b8c1e2d
Revises: 03992129c19c
Create Date: 2026-07-21 10:47:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '44a90b8c1e2d'
down_revision: Union[str, None] = '03992129c19c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_player2_id ON matches(player2_id)")
    op.execute("CREATE INDEX IF NOT EXISTS ix_matches_winner_id ON matches(winner_id)")


def downgrade() -> None:
    op.execute("DROP INDEX IF EXISTS ix_matches_winner_id")
    op.execute("DROP INDEX IF EXISTS ix_matches_player2_id")
