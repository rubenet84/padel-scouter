"""
Endpoints CRUD de torneos: crear, listar, obtener, actualizar y eliminar.

Los torneos son compartibles entre usuarios vía unicidad global por
nombre + fecha. Cada torneo puede tener puntos FEP asociados que se
distribuyen entre los jugadores según la ronda alcanzada.

Arquitectura: Capa API — orquestación con validación de permisos y
delegación a modelos SQLAlchemy. La lógica de rondas y FEP se maneja
en app/domain/value_objects/rounds.py y app/domain/value_objects/fep.py.
"""
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import and_, func, or_
from sqlalchemy.orm import Session

from app.core.dependencies import require_permission
from app.domain.authorization.policy import Permission
from app.services import access_service
from app.infrastructure.database.models import (
    TournamentModel, UserModel, MatchModel, PlayerModel,
)
from app.infrastructure.database.session import get_db
from app.schemas.tournament import (
    TournamentCreateSchema,
    TournamentUpdateSchema,
    TournamentPublicSchema,
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


def _get_tournament_or_404(db: Session, user: UserModel, tournament_id: UUID) -> TournamentModel:
    """Carga un torneo comprobando ownership/scope (admin GLOBAL; resto OWN).

    Recurso ajeno o inexistente → 404 (no revela existencia).
    """
    tournament = db.query(TournamentModel).filter(
        TournamentModel.id == tournament_id
    ).first()
    if tournament is None or not access_service.can_access_owner(user, tournament.owner_id):
        raise HTTPException(status_code=404, detail="Torneo no encontrado")
    return tournament


def _validate_tournament_player(db: Session, player_id: UUID | None, owner_id: UUID) -> None:
    """El `player_id` asignado al torneo debe pertenecer al MISMO owner del torneo.

    Aislamiento estricto: no se permiten torneos cuyo owner sea A y player_id de B.
    Aplica también al admin. Si no se cumple → 404.
    """
    if player_id is None:
        return
    player = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
    if player is None or player.owner_id != owner_id:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")


@router.post("/", response_model=TournamentPublicSchema, status_code=201)
def create_tournament(
    data: TournamentCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.TOURNAMENTS_CREATE)),
):
    """Crea un torneo. El owner es SIEMPRE el usuario autenticado.

    Aislamiento por owner:
    - La unicidad es por (owner_id, name, date): ya NO se reutiliza el torneo de
      otro owner. Dos owners pueden tener "Liga Primavera" el mismo día como
      filas distintas.
    - Si se envía player_id, debe pertenecer al mismo owner del torneo (404 si no).
    El cliente NO puede fijar owner_id (no está en el schema).
    """
    name_clean = data.name.strip()
    owner_id = current_user.id

    # El player_id asignado debe pertenecer al mismo owner que el torneo.
    _validate_tournament_player(db, data.player_id, owner_id)

    # Unicidad por owner + nombre + fecha (aislada por owner; nunca cruza owners).
    existing = db.query(TournamentModel).filter(
        TournamentModel.name == name_clean,
        TournamentModel.date == data.date,
        TournamentModel.owner_id == owner_id,
    ).first()
    if existing:
        return existing

    tournament = TournamentModel(
        name=name_clean,
        date=data.date,
        fep_points=data.fep_points or 0,
        owner_id=owner_id,
        player_id=data.player_id,
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


@router.get("/", response_model=list[TournamentPublicSchema])
def list_tournaments(
    player_id: UUID | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.TOURNAMENTS_READ)),
):
    """Lista torneos según el scope del rol.

    - Sin player_id: admin ve todos; entrenador/jugador solo los suyos.
    - Con player_id: se valida que el jugador sea accesible (404 si ajeno o
      inexistente); admin ve los del jugador de cualquier owner; el resto solo
      si es suyo.

    Aislamiento: nunca se filtra por un owner_id enviado por el cliente.
    """
    is_global = access_service.is_global(current_user)

    if player_id is None:
        query = (
            db.query(TournamentModel, func.count(MatchModel.id).label("match_count"))
            .outerjoin(MatchModel, MatchModel.tournament_id == TournamentModel.id)
        )
        if not is_global:
            query = query.filter(TournamentModel.owner_id == current_user.id)
    else:
        # Validar accesibilidad del jugador (404 si inexistente o ajeno)
        player = db.query(PlayerModel).filter(PlayerModel.id == player_id).first()
        if player is None or not access_service.can_access_owner(current_user, player.owner_id):
            raise HTTPException(status_code=404, detail="Jugador no encontrado")

        has_player_match = (
            db.query(MatchModel.id)
            .filter(
                MatchModel.tournament_id == TournamentModel.id,
                or_(
                    MatchModel.player1_id == player_id,
                    MatchModel.player2_id == player_id,
                    MatchModel.partner_id == player_id,
                ),
            )
            .correlate(TournamentModel)
            .exists()
        )
        has_any_match = (
            db.query(MatchModel.id)
            .filter(MatchModel.tournament_id == TournamentModel.id)
            .correlate(TournamentModel)
            .exists()
        )
        query = (
            db.query(TournamentModel, func.count(MatchModel.id).label("match_count"))
            .outerjoin(MatchModel, MatchModel.tournament_id == TournamentModel.id)
            .filter(or_(
                has_player_match,
                TournamentModel.player_id == player_id,
                and_(TournamentModel.player_id.is_(None), ~has_any_match),
            ))
        )
        if not is_global:
            query = query.filter(TournamentModel.owner_id == current_user.id)

    results = query.group_by(TournamentModel.id).order_by(TournamentModel.date.desc()).all()

    return [
        TournamentPublicSchema(
            id=t.id,
            name=t.name,
            date=t.date,
            fep_points=t.fep_points,
            owner_id=t.owner_id,
            player_id=t.player_id,
            created_at=t.created_at,
            match_count=match_count,
        )
        for t, match_count in results
    ]


@router.get("/{tournament_id}", response_model=TournamentPublicSchema)
def get_tournament(
    tournament_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.TOURNAMENTS_READ)),
):
    """Obtiene un torneo por ID con comprobación de ownership/scope.

    Admin (GLOBAL) accede a cualquiera; entrenador/jugador solo a los suyos.
    Torneo ajeno o inexistente → 404 (no revela existencia ni datos).
    """
    tournament = _get_tournament_or_404(db, current_user, tournament_id)

    match_count = (
        db.query(func.count(MatchModel.id))
        .filter(MatchModel.tournament_id == tournament_id)
        .scalar()
        or 0
    )

    return TournamentPublicSchema(
        id=tournament.id,
        name=tournament.name,
        date=tournament.date,
        fep_points=tournament.fep_points,
        owner_id=tournament.owner_id,
        player_id=tournament.player_id,
        created_at=tournament.created_at,
        match_count=match_count,
    )


@router.put("/{tournament_id}", response_model=TournamentPublicSchema)
def update_tournament(
    tournament_id: UUID,
    data: TournamentUpdateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.TOURNAMENTS_UPDATE)),
):
    """Actualiza nombre, fecha y/o puntos FEP de un torneo.

    Verifica permiso + ownership/scope (admin GLOBAL; resto OWN). Ajeno o
    inexistente → 404. Si se cambia el nombre, actualiza el campo legacy
    `torneo` de los partidos asociados. La validación de duplicados se acota
    al MISMO owner del torneo.
    """
    tournament = _get_tournament_or_404(db, current_user, tournament_id)

    effective_name = tournament.name
    owner_id = tournament.owner_id

    def _dup_filter(name, date, exclude_id):
        f = [
            TournamentModel.name == name,
            TournamentModel.date == date,
            TournamentModel.owner_id == owner_id,
            TournamentModel.id != exclude_id,
        ]
        return f

    if data.name is not None and data.name != tournament.name:
        effective_name = data.name
        effective_date = data.date if data.date is not None else tournament.date
        dup = db.query(TournamentModel).filter(
            *_dup_filter(effective_name, effective_date, tournament_id)
        ).first()
        if dup:
            raise HTTPException(
                status_code=400,
                detail="Ya existe otro torneo con ese nombre y fecha para este jugador.",
            )
        tournament.name = effective_name
        db.query(MatchModel).filter(
            MatchModel.tournament_id == tournament_id,
        ).update({"torneo": effective_name})

    if data.date is not None and data.date != tournament.date:
        dup = db.query(TournamentModel).filter(
            *_dup_filter(effective_name, data.date, tournament_id)
        ).first()
        if dup:
            raise HTTPException(
                status_code=400,
                detail="Ya existe otro torneo con ese nombre y fecha para este jugador.",
            )
        tournament.date = data.date

    if data.fep_points is not None:
        tournament.fep_points = data.fep_points

    db.commit()
    db.refresh(tournament)

    match_count = (
        db.query(func.count(MatchModel.id))
        .filter(MatchModel.tournament_id == tournament_id)
        .scalar()
        or 0
    )

    return TournamentPublicSchema(
        id=tournament.id,
        name=tournament.name,
        date=tournament.date,
        fep_points=tournament.fep_points,
        owner_id=tournament.owner_id,
        player_id=tournament.player_id,
        created_at=tournament.created_at,
        match_count=match_count,
    )


@router.delete("/{tournament_id}", status_code=204)
def delete_tournament(
    tournament_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(require_permission(Permission.TOURNAMENTS_DELETE)),
):
    """Elimina un torneo (hard delete) solo si no tiene partidos asociados.

    Verifica permiso + ownership/scope (admin GLOBAL; resto OWN). Ajeno o
    inexistente → 404. Mantiene la regla funcional: no se puede eliminar si
    tiene partidos. No hay soft delete ni restore.
    """
    tournament = _get_tournament_or_404(db, current_user, tournament_id)

    match_count = (
        db.query(func.count(MatchModel.id))
        .filter(MatchModel.tournament_id == tournament_id)
        .scalar()
        or 0
    )
    if match_count > 0:
        raise HTTPException(
            status_code=400,
            detail=f"No se puede eliminar el torneo porque tiene {match_count} partido(s) asociado(s). Eliminá los partidos primero.",
        )

    db.delete(tournament)
    db.commit()
