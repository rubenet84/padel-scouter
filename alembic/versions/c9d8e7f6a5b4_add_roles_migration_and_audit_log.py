"""add roles migration and audit log

Revision ID: c9d8e7f6a5b4
Revises: 66b9d0e3f4a5
Create Date: 2026-10-05 12:00:00.000000

Fase 2 del sistema de roles de Padel Scouter:

1. Migración FAIL-SAFE de roles de los usuarios existentes:
   - ruben829@msn.com        : viewer -> admin
   - pfararodriguez@gmail.com: viewer -> entrenador

   La migración comprueba las precondiciones ANTES de modificar nada. Si el
   estado real (usuarios/roles) no coincide exactamente con lo esperado, aborta
   con RuntimeError sin aplicar ningún cambio. NO convierte roles desconocidos.

2. Creación de la tabla audit_log para registrar acciones administrativas
   sensibles (cambio de rol, suspensión/reactivación, etc.).

NOTA: la CHECK constraint de users.role se añade en la Fase 3, junto con el
cambio de register() para crear usuarios como 'jugador'. Añadirla ahora
rompería el registro actual (que escribe 'viewer').
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c9d8e7f6a5b4'
down_revision: Union[str, None] = '66b9d0e3f4a5'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


# Rol destino por email para usuarios conocidos. Cualquier usuario fuera de
# este mapa, o cualquier rol actual distinto del esperado, aborta la migración.
EXPECTED_ROLE_MAP: dict[str, str] = {
    "ruben829@msn.com": "admin",
    "pfararodriguez@gmail.com": "entrenador",
}

# Estado previo esperado de TODOS los usuarios (antes de esta migración).
PRE_MIGRATION_ROLE = "viewer"


def _read_current_users(bind) -> dict[str, str]:
    """Devuelve {email: role} de la tabla public.users."""
    rows = bind.execute(sa.text("SELECT email, role FROM public.users")).fetchall()
    return {email: role for email, role in rows}


def _validate_preconditions(current: dict[str, str]) -> list[str]:
    """Comprueba que el estado actual coincide con las precondiciones.

    Devuelve una lista de problemas encontrados (vacía si todo es correcto).
    """
    problems: list[str] = []

    unexpected_roles = {
        email: role
        for email, role in current.items()
        if role != PRE_MIGRATION_ROLE
    }
    if unexpected_roles:
        problems.append(
            f"Roles inesperados (se esperaba '{PRE_MIGRATION_ROLE}'): {unexpected_roles}"
        )

    known = set(EXPECTED_ROLE_MAP)
    present = set(current)

    extra_users = present - known
    if extra_users:
        problems.append(f"Usuarios no previstos: {sorted(extra_users)}")

    missing_users = known - present
    if missing_users:
        problems.append(f"Usuarios esperados ausentes: {sorted(missing_users)}")

    return problems


def upgrade() -> None:
    bind = op.get_bind()

    current = _read_current_users(bind)
    problems = _validate_preconditions(current)
    if problems:
        raise RuntimeError(
            "Migración de roles ABORTADA: las precondiciones no se cumplen y no "
            "se aplicó ningún cambio. Detalle: " + " | ".join(problems)
        )

    # Aplicar únicamente los roles de los usuarios conocidos. Nada más se toca.
    for email, new_role in EXPECTED_ROLE_MAP.items():
        bind.execute(
            sa.text("UPDATE public.users SET role = :role WHERE email = :email"),
            {"role": new_role, "email": email},
        )

    # Tabla de auditoría de acciones administrativas sensibles.
    op.create_table(
        'audit_log',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('actor_id', sa.UUID(), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('action', sa.String(50), nullable=False),
        sa.Column('target_type', sa.String(30), nullable=False),
        sa.Column('target_id', sa.UUID(), nullable=True),
        sa.Column('details', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('ix_audit_log_created_at', 'audit_log', ['created_at'])
    op.create_index('ix_audit_log_actor_id', 'audit_log', ['actor_id'])


def downgrade() -> None:
    """Revierte únicamente la estructura creada por esta migración.

    NO se revierten los roles: hacerlo destruiría cambios legítimos realizados
    posteriormente desde la administración (promociones, degradaciones, etc.).
    La reversión de datos de rol debe ser una decisión administrativa explícita,
    no un efecto automático de un downgrade.
    """
    op.drop_index('ix_audit_log_actor_id', table_name='audit_log')
    op.drop_index('ix_audit_log_created_at', table_name='audit_log')
    op.drop_table('audit_log')
