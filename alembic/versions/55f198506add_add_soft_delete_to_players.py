"""add soft delete to players

Revision ID: 55f198506add
Revises: 7e5d30c40d8b
Create Date: 2026-07-16 15:35:19.501821

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '55f198506add'
down_revision: Union[str, None] = '7e5d30c40d8b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('players', sa.Column('is_deleted', sa.Boolean(), server_default=sa.text('false'), nullable=False))
    op.add_column('players', sa.Column('deleted_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('players', 'deleted_at')
    op.drop_column('players', 'is_deleted')
