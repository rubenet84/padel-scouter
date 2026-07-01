import os
import uuid as uuid_lib
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from app.infrastructure.database.models import PlayerModel, UserModel, MatchModel, TournamentModel
from app.schemas.player import (
    PlayerCreateSchema, PlayerPublicSchema,
    MatchCreateSchema, MatchPublicSchema,
    ComputedStatsSchema,
)

# ── Round hierarchy (lower index = earlier round, single-elimination) ──
ROUND_ORDER = [
    'Fase de grupos',
    '32avos',
    '16avos',
    'Octavos',
    'Cuartos',
    'Semifinal',
    'Final',
]

def get_round_index(round_name: str) -> int:
    try:
        return ROUND_ORDER.index(round_name)
    except ValueError:
        return -1
from app.domain.value_objects.computed_stats import get_computed_stats

from PIL import Image, UnidentifiedImageError
import io

AVATAR_DIR = "app/static/avatars"
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_DIM = 2048

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


# ── Computed Stats ─────────────────────────────────────────────

@router.get("/{player_id}/stats", response_model=ComputedStatsSchema)
def get_player_stats(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Devuelve estadísticas competitivas computadas desde partidos y torneos reales.

    OWASP:
      - A01: Ownership check — el usuario solo ve stats de sus jugadores
      - A07: JWT requerido
      - A03: player_id validado como UUID por FastAPI; query parametrizada
    """
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    return get_computed_stats(db, player_id)


# ── Avatar ──────────────────────────────────────────────────────

@router.post("/{player_id}/avatar", response_model=PlayerPublicSchema)
def upload_avatar(
    player_id: UUID,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Upload avatar for a player.

    OWASP Top 10 protections applied:
    - A01 (Broken Access Control): verify ownership
    - A03 (Injection): re-encode image, strip EXIF, rename file
    - A05 (Security Misconfiguration): static dir, no execution
    - A06 (Vulnerable Components): safe Pillow usage
    - A07 (Authentication): JWT required
    """
    # A07: Auth + A01: Ownership check
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    # A03: reject empty or oversized
    file.file.seek(0)
    contents = file.file.read()
    if len(contents) == 0:
        raise HTTPException(status_code=400, detail="Archivo vacío")
    if len(contents) > MAX_AVATAR_SIZE:
        raise HTTPException(status_code=400, detail="Archivo demasiado grande (máx 5MB)")

    # A03: validate extension
    ext = os.path.splitext(file.filename or "")[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"Formato no permitido: {ext}. Usá JPG, PNG, GIF o WebP.")

    # A03: validate & re-encode with Pillow (strips EXIF/metadata)
    try:
        img = Image.open(io.BytesIO(contents))
        img.verify()  # quick structural check
    except (UnidentifiedImageError, Exception):
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")

    # Re-open after verify (verify consumes the file)
    img = Image.open(io.BytesIO(contents))

    # A03: convert to RGB (strip EXIF, alpha, etc.)
    if img.mode in ("RGBA", "P"):
        img = img.convert("RGBA")
    else:
        img = img.convert("RGB")

    # A03: resize if too large
    if img.width > MAX_DIM or img.height > MAX_DIM:
        img.thumbnail((MAX_DIM, MAX_DIM), Image.LANCZOS)

    # Rename to UUID to prevent path traversal / name collision
    out_name = f"{uuid_lib.uuid4().hex}{ext}"
    out_path = os.path.join(AVATAR_DIR, out_name)

    # Save re-encoded image (strips all EXIF/metadata automatically)
    if img.mode == "RGBA":
        img.save(out_path, "PNG")
        avatar_url = f"/static/avatars/{out_name}"
    else:
        img.save(out_path, "JPEG", quality=85)
        avatar_url = f"/static/avatars/{out_name}"

    # Remove old avatar if exists
    if player.avatar_url:
        old_path = os.path.join("app", player.avatar_url.lstrip("/"))
        if os.path.exists(old_path):
            os.remove(old_path)

    # Save to DB
    player.avatar_url = avatar_url
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

    # Verify tournament ownership if provided
    legacy_torneo = None
    if data.tournament_id is not None:
        tournament = db.query(TournamentModel).filter(
            TournamentModel.id == data.tournament_id,
            TournamentModel.owner_id == current_user.id,
        ).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")
        legacy_torneo = tournament.name  # set legacy torneo field for backward compat

        # Validar ronda
        if data.ronda:
            round_idx = get_round_index(data.ronda)
            if round_idx >= 0:
                # Regla 1: si hay derrota en ronda INFERIOR, no se puede jugar después
                lower_loss = db.query(MatchModel).filter(
                    or_(
                        MatchModel.player1_id == player_id,
                        MatchModel.player2_id == player_id,
                    ),
                    MatchModel.tournament_id == data.tournament_id,
                    MatchModel.ganado == False,
                    MatchModel.ronda.in_(ROUND_ORDER[:round_idx]),
                ).first()
                if lower_loss:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Este jugador ya perdió en {lower_loss.ronda}. No puede haber partidos en rondas posteriores.",
                    )

                # Regla 2: si es derrota, no puede haber partidos GANADOS en rondas superiores
                if data.ganado is False:
                    higher_win = db.query(MatchModel).filter(
                        or_(
                            MatchModel.player1_id == player_id,
                            MatchModel.player2_id == player_id,
                        ),
                        MatchModel.tournament_id == data.tournament_id,
                        MatchModel.ganado == True,
                        MatchModel.ronda.in_(ROUND_ORDER[round_idx + 1:]),
                    ).first()
                    if higher_win:
                        raise HTTPException(
                            status_code=400,
                            detail=f"No se puede marcar como derrota porque hay partidos ganados en rondas superiores. Eliminá primero esos partidos.",
                        )

            # Regla 3: no duplicar ronda en el mismo torneo
            existing = db.query(MatchModel).filter(
                or_(
                    MatchModel.player1_id == player_id,
                    MatchModel.player2_id == player_id,
                ),
                MatchModel.tournament_id == data.tournament_id,
                MatchModel.ronda == data.ronda,
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un partido en {data.ronda} para este torneo. Solo se puede editar o eliminar.",
                )

    match = MatchModel(
        player1_id=player_id,
        player2_id=player_id,       # self-reference OK para partidos individuales
        rival_nombre=data.rival_nombre,
        tournament_id=data.tournament_id,
        ronda=data.ronda,
        torneo=legacy_torneo,
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
    tournament_id: str | None = None,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    query = db.query(MatchModel).filter(
        or_(
            MatchModel.player1_id == player_id,
            MatchModel.player2_id == player_id,
        )
    )

    if tournament_id is not None:
        if tournament_id == "none":
            # Filter amistosos only (no tournament)
            query = query.filter(MatchModel.tournament_id.is_(None))
        else:
            # Filter by specific tournament UUID
            try:
                tid = UUID(tournament_id)
            except ValueError:
                raise HTTPException(status_code=400, detail="tournament_id inválido")
            query = query.filter(MatchModel.tournament_id == tid)

    matches = query.order_by(MatchModel.played_at.desc()).limit(20).all()
    return matches


@router.put("/{player_id}/matches/{match_id}", response_model=MatchPublicSchema)
def update_match(
    player_id: UUID,
    match_id: UUID,
    data: MatchCreateSchema,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Update an existing match."""
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    match = db.query(MatchModel).filter(
        MatchModel.id == match_id,
        or_(
            MatchModel.player1_id == player_id,
            MatchModel.player2_id == player_id,
        )
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    # Verify tournament ownership if provided
    legacy_torneo = None
    if data.tournament_id is not None:
        tournament = db.query(TournamentModel).filter(
            TournamentModel.id == data.tournament_id,
            TournamentModel.owner_id == current_user.id,
        ).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")
        legacy_torneo = tournament.name

        # Validar ronda
        if data.ronda:
            round_idx = get_round_index(data.ronda)
            if round_idx >= 0:
                # Regla 1: si cambió de ronda y hay derrota en ronda INFERIOR, no se puede pasar después
                if data.ronda != match.ronda:
                    lower_loss = db.query(MatchModel).filter(
                        or_(
                            MatchModel.player1_id == player_id,
                            MatchModel.player2_id == player_id,
                        ),
                        MatchModel.tournament_id == data.tournament_id,
                        MatchModel.ganado == False,
                        MatchModel.ronda.in_(ROUND_ORDER[:round_idx]),
                        MatchModel.id != match_id,
                    ).first()
                    if lower_loss:
                        raise HTTPException(
                            status_code=400,
                            detail=f"Este jugador ya perdió en {lower_loss.ronda}. No puede haber partidos en rondas posteriores.",
                        )

                # Regla 2: si se cambia a derrota, no puede haber partidos GANADOS en rondas superiores
                if data.ganado is False and match.ganado is not False:
                    higher_win = db.query(MatchModel).filter(
                        or_(
                            MatchModel.player1_id == player_id,
                            MatchModel.player2_id == player_id,
                        ),
                        MatchModel.tournament_id == data.tournament_id,
                        MatchModel.ganado == True,
                        MatchModel.ronda.in_(ROUND_ORDER[round_idx + 1:]),
                        MatchModel.id != match_id,
                    ).first()
                    if higher_win:
                        raise HTTPException(
                            status_code=400,
                            detail=f"No se puede marcar como derrota porque hay partidos ganados en rondas superiores. Eliminá primero esos partidos.",
                        )

            # Regla 3: no duplicar ronda en el mismo torneo (excluyendo este partido)
            if data.ronda != match.ronda or data.tournament_id != match.tournament_id:
                existing = db.query(MatchModel).filter(
                    or_(
                        MatchModel.player1_id == player_id,
                        MatchModel.player2_id == player_id,
                    ),
                    MatchModel.tournament_id == data.tournament_id,
                    MatchModel.ronda == data.ronda,
                    MatchModel.id != match_id,
                ).first()
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Ya existe otro partido en {data.ronda} para este torneo.",
                    )

    # Update fields
    match.rival_nombre = data.rival_nombre
    match.tournament_id = data.tournament_id
    match.ronda = data.ronda
    match.torneo = legacy_torneo  # may be None for amistosos
    match.resultado = data.resultado
    match.result = data.resultado  # keep legacy field in sync
    match.ganado = data.ganado
    match.scoring_method = data.scoring_method
    match.winner_id = player_id if data.ganado else None
    if data.notes:
        match.notes = data.notes

    db.commit()
    db.refresh(match)
    return match


@router.delete("/{player_id}/matches/{match_id}", status_code=204)
def delete_match(
    player_id: UUID,
    match_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Delete a match."""
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    match = db.query(MatchModel).filter(
        MatchModel.id == match_id,
        or_(
            MatchModel.player1_id == player_id,
            MatchModel.player2_id == player_id,
        )
    ).first()
    if not match:
        raise HTTPException(status_code=404, detail="Partido no encontrado")

    db.delete(match)
    db.commit()
