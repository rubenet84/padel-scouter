"""add golpe_descripcion and golpe_puntuacion to analyses

Revision ID: a8f3c2d1e4b5
Revises: 5b1dcc84d45e
Create Date: 2026-06-28 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a8f3c2d1e4b5"
down_revision: Union[str, None] = "5b1dcc84d45e"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("analyses", sa.Column("golpe_descripcion", sa.Text(), nullable=True))
    op.add_column("analyses", sa.Column("golpe_puntuacion", sa.Integer(), nullable=True))


def downgrade() -> None:
    op.drop_column("analyses", "golpe_puntuacion")
    op.drop_column("analyses", "golpe_descripcion")
