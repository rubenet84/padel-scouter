from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user, require_role
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import PlayerModel, UserModel
from app.schemas.player import PlayerCreateSchema, PlayerPublicSchema
from app.domain.entities.player import Player, PlayerStats

router = APIRouter(prefix="/players", tags=["players"])


def _model_to_entity(p: PlayerModel) -> Player:
    stats = PlayerStats(
        derecha=p.derecha, reves=p.reves, volea=p.volea,
        bandeja=p.bandeja, vibora=p.vibora, smash=p.smash,
        lob=p.lob, saque=p.saque, bajada_pared=p.bajada_pared,
        velocidad=p.velocidad, resistencia=p.resistencia,
        reflejos=p.reflejos, tactica=p.tactica, presion=p.presion,
        trabajo_en_pareja=p.trabajo_en_pareja,
        torneos_jugados=p.torneos_jugados, victorias=p.victorias,
        puntos_ranking_fep=p.puntos_ranking_fep,
    )
    return Player(id=p.id, name=p.name, category=p.category, stats=stats)


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