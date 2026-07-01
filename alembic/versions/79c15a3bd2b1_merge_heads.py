"""merge_heads

Revision ID: 79c15a3bd2b1
Revises: a8f3c2d1e4b5, d4e5f6a7b8c9
Create Date: 2026-06-30 10:53:07.966968

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '79c15a3bd2b1'
down_revision: Union[str, None] = ('a8f3c2d1e4b5', 'd4e5f6a7b8c9')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass