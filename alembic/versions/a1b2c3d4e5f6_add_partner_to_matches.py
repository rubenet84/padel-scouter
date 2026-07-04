"""add_partner_to_matches

Revision ID: a1b2c3d4e5f6
Revises: 79c15a3bd2b1
Create Date: 2026-07-03 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '1d19e414c1dc'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('matches',
        sa.Column('partner_id', postgresql.UUID(as_uuid=True), nullable=True)
    )
    op.add_column('matches',
        sa.Column('partner_nombre', sa.String(150), nullable=True)
    )
    op.create_foreign_key(
        'fk_match_partner', 'matches', 'players',
        ['partner_id'], ['id']
    )


def downgrade() -> None:
    op.drop_constraint('fk_match_partner', 'matches', type_='foreignkey')
    op.drop_column('matches', 'partner_nombre')
    op.drop_column('matches', 'partner_id')
