"""drop_competitive_fields_from_players — Phase 5: remove deprecated competitive columns

Revision ID: d4e5f6a7b8c9
Revises: 3c101144546e
Create Date: 2026-06-29 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "d4e5f6a7b8c9"
down_revision: Union[str, None] = "3c101144546e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_column("players", "torneos_jugados")
    op.drop_column("players", "victorias")
    op.drop_column("players", "puntos_ranking_fep")


def downgrade() -> None:
    op.add_column("players", sa.Column("torneos_jugados", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("players", sa.Column("victorias", sa.Integer(), nullable=False, server_default="0"))
    op.add_column("players", sa.Column("puntos_ranking_fep", sa.Integer(), nullable=False, server_default="0"))
