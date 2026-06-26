from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import PlayerModel, UserModel, MatchModel
from app.schemas.player import (
    PlayerCreateSchema, PlayerPublicSchema,
    MatchCreateSchema, MatchPublicSchema,
)

router = APIRouter(prefix="/players", tags=["players"])


# ── Players CRUD ──────────────────────────────────────────────

@router.post("/", response_model=PlayerPublicSchema, status_code=201)
def create_player(
    data: PlayerCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = PlayerModel(
        name=data.name,
        category=data.category,
        owner_id=current_user.id,
        **data.stats.model_dump(),
    )
    db.add(player)
    db.commit()
    db.refresh(player)
    return player


@router.get("/", response_model=list[PlayerPublicSchema])
def list_players(
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    return db.query(PlayerModel).filter(
        PlayerModel.owner_id == current_user.id
    ).all()


@router.get("/{player_id}", response_model=PlayerPublicSchema)
def get_player(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    return player


@router.put("/{player_id}", response_model=PlayerPublicSchema)
def update_player(
    player_id: UUID,
    data: PlayerCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    player.name     = data.name
    player.category = data.category
    for field, val in data.stats.model_dump().items():
        setattr(player, field, val)

    db.commit()
    db.refresh(player)
    return player


@router.delete("/{player_id}", status_code=204)
def delete_player(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    db.delete(player)
    db.commit()


# ── Matches ───────────────────────────────────────────────────

@router.post("/{player_id}/matches", response_model=MatchPublicSchema, status_code=201)
def add_match(
    player_id: UUID,
    data: MatchCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    match = MatchModel(
        player1_id=player_id,
        player2_id=player_id,       # self-reference OK para partidos individuales
        rival_nombre=data.rival_nombre,
        torneo=data.torneo,
        resultado=data.resultado,
        ganado=data.ganado,
        scoring_method=data.scoring_method,
        result=data.resultado,      # campo legacy del modelo
        winner_id=player_id if data.ganado else None,
        notes=data.notes,
    )
    db.add(match)
    db.commit()
    db.refresh(match)
    return match


@router.get("/{player_id}/matches", response_model=list[MatchPublicSchema])
def get_matches(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    matches = db.query(MatchModel).filter(
        or_(
            MatchModel.player1_id == player_id,
            MatchModel.player2_id == player_id,
        )
    ).order_by(MatchModel.played_at.desc()).limit(20).all()
    return matches