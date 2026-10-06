"""Repositorio de auditoría — persiste acciones administrativas sensibles.

Las entradas se añaden con flush (no commit): la transacción la controla el
llamador, de modo que la auditoría se confirma junto con la acción auditada.
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.infrastructure.database.models import AuditLogModel


def add_audit_entry(
    db: Session,
    actor_id: UUID,
    action: str,
    target_type: str,
    target_id: UUID | None = None,
    details: str | None = None,
) -> AuditLogModel:
    """Añade una entrada de auditoría (sin commit). Devuelve el modelo creado."""
    entry = AuditLogModel(
        actor_id=actor_id,
        action=action,
        target_type=target_type,
        target_id=target_id,
        details=details,
    )
    db.add(entry)
    db.flush()
    return entry
