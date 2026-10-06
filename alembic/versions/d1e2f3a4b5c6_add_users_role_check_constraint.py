"""add users role check constraint

Revision ID: d1e2f3a4b5c6
Revises: c9d8e7f6a5b4
Create Date: 2026-10-05 13:00:00.000000

Fase 3 del sistema de roles de Padel Scouter: incorpora la restricción de
valores permitidos para users.role.

Reglas:
- Antes de crear la constraint, verifica que no queden valores inválidos
  (p. ej. 'viewer' u otros). Si los hay, aborta sin aplicar cambios.
- La constraint es: role IN ('admin', 'entrenador', 'jugador').
- No modifica los roles existentes (admin / entrenador se conservan).
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd1e2f3a4b5c6'
down_revision: Union[str, None] = 'c9d8e7f6a5b4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


ALLOWED_ROLES = ("admin", "entrenador", "jugador")
CONSTRAINT_NAME = "ck_users_role"


def upgrade() -> None:
    bind = op.get_bind()

    # Precondición fail-safe: no debe haber roles fuera del conjunto permitido.
    invalid = bind.execute(
        sa.text(
            "SELECT email, role FROM public.users "
            "WHERE role NOT IN ('admin', 'entrenador', 'jugador')"
        )
    ).fetchall()
    if invalid:
        raise RuntimeError(
            "No se puede añadir la CHECK constraint de users.role: existen roles "
            f"inválidos que deben resolverse primero: {[tuple(r) for r in invalid]}"
        )

    op.create_check_constraint(
        CONSTRAINT_NAME,
        "users",
        "role IN ('admin', 'entrenador', 'jugador')",
    )


def downgrade() -> None:
    op.drop_constraint(CONSTRAINT_NAME, "users", type_="check")
