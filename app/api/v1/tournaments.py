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

from app.core.dependencies import get_current_user
from app.infrastructure.database.models import (
    TournamentModel, UserModel, MatchModel,
)
from app.infrastructure.database.session import get_db
from app.schemas.tournament import (
    TournamentCreateSchema,
    TournamentUpdateSchema,
    TournamentPublicSchema,
)

router = APIRouter(prefix="/tournaments", tags=["tournaments"])


@router.post("/", response_model=TournamentPublicSchema, status_code=201)
def create_tournament(
    data: TournamentCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Crear un nuevo torneo. Si se pasa player_id, el torneo se asigna
    a ese jugador y la unicidad es por nombre + fecha + player_id.

    Unicidad global: si ya existe un torneo con el mismo nombre y fecha,
    se devuelve el existente en lugar de crear un duplicado. Esto permite
    que múltiples usuarios compartan el mismo torneo.

    OWASP:
      - A01 (Broken Access Control): owner_id = current_user.id
      - A03 (Injection): name validado por Pydantic (strip_html, max_length)
      - A07 (Authentication): JWT requerido
    """
    name_clean = data.name.strip()

    # Unicidad GLOBAL por nombre + fecha: si alguien ya creó un torneo
    # con el mismo nombre y fecha, lo reutilizamos en vez de duplicar.
    existing = db.query(TournamentModel).filter(
        TournamentModel.name == name_clean,
        TournamentModel.date == data.date,
    ).first()
    if existing:
        return existing

    tournament = TournamentModel(
        name=name_clean,
        date=data.date,
        fep_points=data.fep_points or 0,
        owner_id=current_user.id,
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
    current_user: UserModel = Depends(get_current_user),
):
    """
    Listar torneos.

    Si se pasa player_id, devuelve torneos donde ese jugador participa:
      - Torneos donde el jugador tiene partidos
      - Torneos asignados al jugador (player_id = X)
      - Torneos sin asignar ni partidos (asignables)

    Si no se pasa player_id, devuelve torneos creados por el usuario actual.

    Incluye match_count para cada torneo vía agregación SQL.

    OWASP:
      - A01: scoped by player_id or ownership
      - A07: JWT requerido
    """
    if player_id is None:
        # Fallback: torneos creados por el usuario actual
        query = (
            db.query(TournamentModel, func.count(MatchModel.id).label("match_count"))
            .outerjoin(MatchModel, MatchModel.tournament_id == TournamentModel.id)
            .filter(TournamentModel.owner_id == current_user.id)
        )
    else:
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
    current_user: UserModel = Depends(get_current_user),
):
    """
    Obtener un torneo por ID (acceso global por nombre+fecha).

    OWASP:
      - A07: JWT requerido
    """
    tournament = (
        db.query(TournamentModel)
        .filter(
            TournamentModel.id == tournament_id,
        )
        .first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

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
    current_user: UserModel = Depends(get_current_user),
):
    """
    Actualizar nombre, fecha y/o puntos FEP de un torneo.

    Si se cambia el nombre, se actualiza automáticamente el campo
    `torneo` (legacy) en todos los partidos asociados.

    La validación de duplicados respeta el player_id del torneo.

    OWASP:
      - A01: ownership check antes de mutar
      - A03: input validado por Pydantic
      - A07: JWT requerido
    """
    tournament = (
        db.query(TournamentModel)
        .filter(
            TournamentModel.id == tournament_id,
            TournamentModel.owner_id == current_user.id,
        )
        .first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

    effective_name = tournament.name

    def _dup_filter(name, date, exclude_id):
        f = [
            TournamentModel.name == name,
            TournamentModel.date == date,
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
    current_user: UserModel = Depends(get_current_user),
):
    """
    Eliminar un torneo solo si no tiene partidos asociados.
    Si el torneo tiene player_id, solo revisa partidos de ESE jugador.
    Si no tiene player_id (legacy), revisa todos los partidos.

    OWASP:
      - A01: ownership check antes de eliminar
      - A03: consulta parametrizada (SQLAlchemy ORM)
      - A07: JWT requerido
    """
    tournament = (
        db.query(TournamentModel)
        .filter(
            TournamentModel.id == tournament_id,
            TournamentModel.owner_id == current_user.id,
        )
        .first()
    )
    if not tournament:
        raise HTTPException(status_code=404, detail="Torneo no encontrado")

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
