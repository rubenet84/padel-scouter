"""Add all missing columns present in SQLAlchemy model but not in migrations

Revision ID: 66b9d0e3f4a5
Revises: 44a90b8c1e2d
Create Date: 2026-07-23 10:20:00.000000

This migration adds ALL columns that exist in the PlayerModel SQLAlchemy
definition but were never captured by Alembic migrations (they were only
created by Base.metadata.create_all() in development).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = '66b9d0e3f4a5'
down_revision: Union[str, None] = '44a90b8c1e2d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Columnas de técnica que faltan en la migración inicial
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS volea_derecha INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS volea_reves INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS remate INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS globo INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS vibora INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS bandeja INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS saque INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS bajada_pared INTEGER DEFAULT 50")
    # Columnas de físico
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS velocidad INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS resistencia INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS reflejos INTEGER DEFAULT 50")
    # Columnas mentales
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS tactica INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS presion INTEGER DEFAULT 50")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS trabajo_en_pareja INTEGER DEFAULT 50")
    # Avatar y mano
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS avatar_url VARCHAR(500)")
    op.execute("ALTER TABLE players ADD COLUMN IF NOT EXISTS mano VARCHAR(20) DEFAULT 'Derecha'")


def downgrade() -> None:
    pass
