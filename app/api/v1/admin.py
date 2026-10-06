"""Endpoints administrativos de usuarios (exclusivo para rol `admin`).

Reutiliza la infraestructura RBAC existente (`require_permission`) y la
auditoría (`access_service.record_audit`). No introduce un sistema paralelo.

Endpoints:
- GET   /admin/users               -> users.read
- GET   /admin/users/stats         -> users.read
- GET   /admin/users/{id}          -> users.read
- PATCH /admin/users/{id}/role     -> users.change_role (solo jugador<->entrenador)
- PATCH /admin/users/{id}/status   -> users.suspend

Reglas de seguridad:
- Solo `admin` (los permisos users.* son admin-only).
- El rol destino NO puede ser `admin` (fuera del MVP).
- Un admin no puede cambiarse el rol a sí mismo (self-demotion).
- Nunca se puede dejar el sistema con 0 administradores activos
  (bloqueo FOR UPDATE de admins activos para serializar concurrencia).
- Cada cambio real se registra en audit_log; un no-cambio no genera auditoría.
"""
import json
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.domain.authorization.policy import Permission, Role
from app.infrastructure.database.models import (
    UserModel,
    AUDIT_ROLE_CHANGED,
    AUDIT_USER_SUSPENDED,
    AUDIT_USER_REACTIVATED,
)
from app.infrastructure.database.session import get_db
from app.infrastructure.repositories import admin_user_repository as repo
from app.infrastructure.repositories.user_repository import lock_user_by_id
from app.services import access_service
from app.schemas.admin import (
    AdminUserRow,
    AdminUserListResponse,
    AdminUserStats,
    RoleUpdateRequest,
    StatusUpdateRequest,
)

router = APIRouter(prefix="/admin", tags=["admin"])


def _row(row) -> AdminUserRow:
    return AdminUserRow(**dict(row._mapping))


@router.get("/users", response_model=AdminUserListResponse)
def list_users(
    search: str | None = Query(None, max_length=100, description="Buscar por username o email"),
    role: Role | None = Query(None, description="Filtrar por rol"),
    is_active: bool | None = Query(None, description="Filtrar por estado activo/suspendido"),
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.USERS_READ)),
):
    """Listado paginado de usuarios con búsqueda y filtros (solo admin)."""
    role_val = role.value if role else None
    total = repo.count_users(db, search=search, role=role_val, is_active=is_active)
    offset = (page - 1) * page_size
    rows = repo.list_users(
        db, search=search, role=role_val, is_active=is_active, limit=page_size, offset=offset
    )
    total_pages = (total + page_size - 1) // page_size if total > 0 else 0
    return AdminUserListResponse(
        items=[_row(r) for r in rows],
        total=total,
        page=page,
        page_size=page_size,
        total_pages=total_pages,
    )


@router.get("/users/stats", response_model=AdminUserStats)
def users_stats(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.USERS_READ)),
):
    """Totales globales para las tarjetas del panel (solo admin)."""
    s = repo.user_stats(db)
    return AdminUserStats(
        total=s.total, admins=s.admins, entrenadores=s.entrenadores,
        jugadores=s.jugadores, suspended=s.suspended,
    )


@router.get("/users/{user_id}", response_model=AdminUserRow)
def get_user(
    user_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.USERS_READ)),
):
    """Detalle administrativo de un usuario (solo admin). 404 si no existe."""
    row = repo.get_user(db, user_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Usuario no encontrado")
    return _row(row)


@router.patch("/users/{user_id}/role", response_model=AdminUserRow)
def change_role(
    user_id: UUID,
    data: RoleUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.USERS_CHANGE_ROLE)),
):
    """Cambia el rol entre `jugador` y `entrenador` (solo admin).

    Rechaza: admin objetivo, self-demotion y valores de rol fuera del MVP.
    Registra auditoría solo si el rol cambia realmente.
    """
    if user_id == current_user.id:
        raise HTTPException(status_code=403, detail="No puedes cambiar tu propio rol")

    # Bloquea la fila del objetivo (serializa cambios de rol sobre el mismo usuario).
    # NO se usa lock_active_admins aquí: los admins no cambian de rol (se rechazan
    # más abajo) y este endpoint no puede reducir el nº de admins activos.
    lock_user_by_id(db, user_id)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    if user.role == Role.ADMIN.value:
        db.rollback()
        raise HTTPException(
            status_code=403,
            detail="La gestión de administradores está fuera del alcance",
        )

    new_role = data.role
    if user.role == new_role:
        db.rollback()  # no hubo cambio real: no se audita
        return _row(repo.get_user(db, user_id))

    previous = user.role
    user.role = new_role
    access_service.record_audit(
        db,
        actor=current_user,
        action=AUDIT_ROLE_CHANGED,
        target_type="user",
        target_id=user.id,
        details=json.dumps({"from": previous, "to": new_role}),
    )
    db.commit()
    return _row(repo.get_user(db, user_id))


@router.patch("/users/{user_id}/status", response_model=AdminUserRow)
def change_status(
    user_id: UUID,
    data: StatusUpdateRequest,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.USERS_SUSPEND)),
):
    """Suspende/activa una cuenta (solo admin), usando UserModel.is_active.

    Nunca deja el sistema sin administradores activos. Audita solo cambios reales.
    """
    # Serializa TODAS las operaciones de estado sobre el conjunto de admins
    # activos con el MISMO SELECT ... FOR UPDATE (mismo orden de bloqueo → sin
    # deadlock). Un solo lock evita la combinación peligrosa lock_user_by_id +
    # lock_active_admins. La comprobación del último admin y el UPDATE quedan en
    # la misma transacción.
    repo.lock_active_admins(db)

    user = db.query(UserModel).filter(UserModel.id == user_id).first()
    if user is None:
        db.rollback()
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    # F2: un admin no puede suspender su propia cuenta, con independencia del
    # número de admins existentes (evita autobloqueo). Reactivar(se) no se bloquea.
    if data.is_active is False and user_id == current_user.id:
        db.rollback()
        raise HTTPException(status_code=403, detail="No puedes suspender tu propia cuenta")

    if user.is_active == data.is_active:
        db.rollback()  # sin cambio real: no se audita
        return _row(repo.get_user(db, user_id))

    if data.is_active is False and user.role == Role.ADMIN.value:
        if repo.count_active_admins(db) <= 1:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail="No se puede suspender al último administrador activo",
            )

    user.is_active = data.is_active
    access_service.record_audit(
        db,
        actor=current_user,
        action=AUDIT_USER_SUSPENDED if data.is_active is False else AUDIT_USER_REACTIVATED,
        target_type="user",
        target_id=user.id,
        details=json.dumps({"is_active": data.is_active}),
    )
    db.commit()
    return _row(repo.get_user(db, user_id))
