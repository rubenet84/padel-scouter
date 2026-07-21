"""Notificaciones — campanita + polling."""
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.infrastructure.database.models import NotificationModel, UserModel
from app.infrastructure.database.session import get_db

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("")
def list_notifications(
    unread_only: bool = Query(False, description="Solo no leídas"),
    player_id: str | None = Query(None, description="Filtrar por jugador"),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Lista notificaciones del usuario, opcionalmente filtradas por jugador."""
    q = db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id
    )
    if player_id:
        q = q.filter(NotificationModel.player_id == player_id)
    if unread_only:
        q = q.filter(NotificationModel.is_read == False)
    q = q.order_by(NotificationModel.is_read.asc(),
                   NotificationModel.created_at.desc())

    items = q.limit(limit).all()
    return [
        {
            "id": str(n.id),
            "type": n.type,
            "title": n.title,
            "message": n.message,
            "related_url": n.related_url,
            "player_id": str(n.player_id) if n.player_id else None,
            "is_read": n.is_read,
            "created_at": n.created_at.isoformat() + 'Z',
        }
        for n in items
    ]


@router.get("/unread-count")
def unread_count(
    player_id: str | None = Query(None, description="Filtrar por jugador"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Contador rápido de no leídas (para polling ligero)."""
    q = db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.is_read == False,
    )
    if player_id:
        q = q.filter(NotificationModel.player_id == player_id)
    count = q.count()
    return {"count": count}


@router.put("/{notification_id}/read")
def mark_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Marca una notificación como leída."""
    n = db.query(NotificationModel).filter(
        NotificationModel.id == notification_id,
        NotificationModel.user_id == current_user.id,
    ).first()
    if not n:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notificación no encontrada")
    n.is_read = True
    db.commit()
    return {"success": True}


@router.put("/read-all")
def mark_all_read(
    player_id: str | None = Query(None, description="Filtrar por jugador"),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Marca todas las notificaciones como leídas."""
    q = db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.is_read == False,
    )
    if player_id:
        q = q.filter(NotificationModel.player_id == player_id)
    q.update({"is_read": True})
    db.commit()
    return {"success": True}
