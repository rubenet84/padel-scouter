"""Add missing volea_derecha and volea_reves columns to players

Revision ID: 55a8c9d1e2f3
Revises: 44a90b8c1e2d
Create Date: 2026-07-23 10:13:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55a8c9d1e2f3'
down_revision: Union[str, None] = '44a90b8c1e2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS volea_derecha INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS volea_reves INTEGER DEFAULT 50")


def downgrade() -> None:
    op.execute("ALTER TABLE players DROP COLUMN IF EXISTS volea_derecha")
    op.execute("ALTER TABLE players DROP COLUMN IF EXISTS volea_reves")
