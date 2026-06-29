from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func
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
    Crear un nuevo torneo.

    OWASP:
      - A01 (Broken Access Control): owner_id = current_user.id
      - A03 (Injection): name validado por Pydantic (strip_html, max_length)
      - A07 (Authentication): JWT requerido
    """
    # Validar: no duplicar nombre + fecha
    name_clean = data.name.strip()
    existing = db.query(TournamentModel).filter(
        TournamentModel.name == name_clean,
        TournamentModel.date == data.date,
        TournamentModel.owner_id == current_user.id,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail="Ya existe un torneo con ese nombre y fecha.",
        )

    tournament = TournamentModel(
        name=name_clean,
        date=data.date,
        fep_points=data.fep_points or 0,
        owner_id=current_user.id,
    )
    db.add(tournament)
    db.commit()
    db.refresh(tournament)
    return tournament


@router.get("/", response_model=list[TournamentPublicSchema])
def list_tournaments(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Listar torneos del usuario autenticado, ordenados por fecha descendente,
    incluyendo la cantidad de partidos asociados a cada uno.

    OWASP:
      - A01: solo torneos del usuario actual
      - A07: JWT requerido
    """
    results = (
        db.query(
            TournamentModel,
            func.count(MatchModel.id).label("match_count"),
        )
        .outerjoin(
            MatchModel, MatchModel.tournament_id == TournamentModel.id
        )
        .filter(TournamentModel.owner_id == current_user.id)
        .group_by(TournamentModel.id)
        .order_by(TournamentModel.date.desc())
        .all()
    )

    return [
        TournamentPublicSchema(
            id=t.id,
            name=t.name,
            date=t.date,
            fep_points=t.fep_points,
            owner_id=t.owner_id,
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
    Obtener un torneo por ID (solo si pertenece al usuario actual).

    OWASP:
      - A01: ownership check
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

    return TournamentPublicSchema(
        id=tournament.id,
        name=tournament.name,
        date=tournament.date,
        fep_points=tournament.fep_points,
        owner_id=tournament.owner_id,
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
    Actualizar fecha y/o puntos FEP de un torneo.

    El nombre es INMUTABLE — no se puede modificar después de la creación.
    Solo se actualizan date y fep_points.

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

    # name is NOT updated — it's immutable
    # Validar: si cambia la fecha, que no choque con otro torneo del mismo nombre
    if data.date != tournament.date:
        dup = db.query(TournamentModel).filter(
            TournamentModel.name == tournament.name,
            TournamentModel.date == data.date,
            TournamentModel.owner_id == current_user.id,
            TournamentModel.id != tournament_id,
        ).first()
        if dup:
            raise HTTPException(
                status_code=400,
                detail="Ya existe otro torneo con ese nombre y fecha.",
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
    Eliminar un torneo. Los partidos asociados mantienen su historial:
    su FK tournament_id se establece a NULL (SET NULL).

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

    # SET NULL on related matches — preserve match history
    db.query(MatchModel).filter(
        MatchModel.tournament_id == tournament_id,
    ).update({"tournament_id": None})

    db.delete(tournament)
    db.commit()
