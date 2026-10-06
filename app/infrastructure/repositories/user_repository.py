"""Repositorio de usuarios — operaciones de acceso a datos para autorización.

Incluye el bloqueo de fila de usuario (SELECT ... FOR UPDATE) usado para
serializar creaciones concurrentes de recursos y evitar condiciones de carrera
en la comprobación de límites.
"""

from uuid import UUID

from sqlalchemy import text
from sqlalchemy.orm import Session


def lock_user_by_id(db: Session, user_id: UUID) -> None:
    """Bloquea la fila del usuario hasta el final de la transacción actual.

    Se usa dentro de la misma transacción que la creación de un recurso para
    serializar operaciones concurrentes del mismo propietario. No hace commit:
    el llamador controla la transacción.
    """
    db.execute(
        text("SELECT id FROM users WHERE id = :uid FOR UPDATE"),
        {"uid": user_id},
    )
