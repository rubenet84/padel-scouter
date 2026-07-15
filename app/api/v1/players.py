import logging
import os
import uuid as uuid_lib
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File

logger = logging.getLogger(__name__)
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user
from app.infrastructure.database.session import get_db
from sqlalchemy import func, desc as sa_desc
from app.infrastructure.database.models import PlayerModel, UserModel, MatchModel, TournamentModel, AnalysisModel
from app.schemas.player import (
    PlayerCreateSchema, PlayerPublicSchema,
    MatchCreateSchema, MatchPublicSchema,
    ComputedStatsSchema, PlayerAnalyticsSchema,
)


from app.domain.value_objects.rounds import ROUND_ORDER, get_round_index
from app.domain.value_objects.computed_stats import get_computed_stats

from PIL import Image, UnidentifiedImageError
import io

AVATAR_DIR = "app/static/avatars"
MAX_AVATAR_SIZE = 5 * 1024 * 1024  # 5MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_DIM = 2048

router = APIRouter(prefix="/players", tags=["players"])


def _player_filter(player_id: UUID):
    """Matches where player participated in any role (creator, self-ref, or partner)."""
    return or_(
        MatchModel.player1_id == player_id,
        MatchModel.player2_id == player_id,
        MatchModel.partner_id == player_id,
    )


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
    players = db.query(PlayerModel).filter(
        PlayerModel.owner_id == current_user.id
    ).all()

    # Enriquecer con el último power_level del análisis IA
    if players:
        pids = [p.id for p in players]
        latest = db.query(
            AnalysisModel.player_id,
            AnalysisModel.power_level,
        ).filter(
            AnalysisModel.player_id.in_(pids)
        ).order_by(
            AnalysisModel.player_id,
            sa_desc(AnalysisModel.created_at)
        ).distinct(AnalysisModel.player_id).all()
        power_map = {row.player_id: row.power_level for row in latest}
        for p in players:
            p.power_level = power_map.get(p.id)

    return players


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


@router.get("/{player_id}/analytics", response_model=PlayerAnalyticsSchema)
def get_player_analytics(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """
    Devuelve estadísticas detalladas de partidos: sets, rondas,
    desglose por torneo, sistema de puntuación, etc.

    OWASP:
      - A01: Ownership check
      - A07: JWT requerido
      - A03: player_id validado como UUID
    """
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    from app.domain.value_objects.analytics import get_match_analytics
    return get_match_analytics(db, player_id)


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
    except UnidentifiedImageError:
        raise HTTPException(status_code=400, detail="El archivo no es una imagen válida")
    except Exception as e:
        logger.error("Error al verificar imagen: %s", e)
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

    # Ensure avatar directory exists
    os.makedirs(AVATAR_DIR, exist_ok=True)

    # Save re-encoded image (strips all EXIF/metadata automatically)
    # Force extension to match actual format saved (E5: no mismatch)
    if img.mode == "RGBA":
        ext = ".png"
        out_name = f"{uuid_lib.uuid4().hex}{ext}"
        out_path = os.path.join(AVATAR_DIR, out_name)
        img.save(out_path, "PNG")
    else:
        ext = ".jpg"
        out_name = f"{uuid_lib.uuid4().hex}{ext}"
        out_path = os.path.join(AVATAR_DIR, out_name)
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

    # Verify tournament exists
    legacy_torneo = None
    if data.tournament_id is not None:
        tournament = db.query(TournamentModel).filter(
            TournamentModel.id == data.tournament_id,
        ).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")
        legacy_torneo = tournament.name  # set legacy torneo field for backward compat

        # Validar ronda
        if data.ronda:
            round_idx = get_round_index(data.ronda)
            if round_idx < 0:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ronda inválida: '{data.ronda}'. Las rondas válidas son: {', '.join(ROUND_ORDER)}",
                )
            if round_idx >= 0:
                # Regla 1: si hay derrota en ronda INFERIOR, no se puede jugar después
                lower_loss = db.query(MatchModel).filter(
                    _player_filter(player_id),
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
                        _player_filter(player_id),
                        MatchModel.tournament_id == data.tournament_id,
                        MatchModel.ganado == True,
                        MatchModel.ronda.in_(ROUND_ORDER[round_idx + 1:]),
                    ).first()
                    if higher_win:
                        raise HTTPException(
                            status_code=400,
                            detail=f"No se puede marcar como derrota porque hay partidos ganados en rondas superiores. Eliminá primero esos partidos.",
                        )

                # Regla 3: no saltar rondas — si ya hay partidos en el torneo, la ronda debe ser consecutiva
                existing_any = db.query(MatchModel).filter(
                    _player_filter(player_id),
                    MatchModel.tournament_id == data.tournament_id,
                ).first()
                if existing_any and round_idx > 0:
                    prev_round = ROUND_ORDER[round_idx - 1]
                    prev_win = db.query(MatchModel).filter(
                        _player_filter(player_id),
                        MatchModel.tournament_id == data.tournament_id,
                        MatchModel.ronda == prev_round,
                        MatchModel.ganado == True,
                    ).first()
                    if not prev_win:
                        raise HTTPException(
                            status_code=400,
                            detail=f"No se puede jugar {data.ronda} sin haber ganado {prev_round} antes. Las rondas deben ser consecutivas.",
                        )

            # Regla 4: no duplicar ronda en el mismo torneo (excluyendo este partido en update)
            existing = db.query(MatchModel).filter(
                _player_filter(player_id),
                MatchModel.tournament_id == data.tournament_id,
                MatchModel.ronda == data.ronda,
            ).first()
            if existing:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un partido en {data.ronda} para este torneo. Solo se puede editar o eliminar.",
                )

    # ── Partner / Compañero logic ───────────────────────────────────
    partner_id = data.partner_id
    partner_nombre = data.partner_nombre

    # Tournament partner locking: if there's an existing match in this tournament
    # with a partner set, auto-fill and reject any new partner value
    if data.tournament_id is not None:
        existing_partner_match = db.query(MatchModel).filter(
            _player_filter(player_id),
            MatchModel.tournament_id == data.tournament_id,
            MatchModel.partner_id.isnot(None),
        ).first()
        if existing_partner_match:
            # Partner is locked for this tournament.
            # Auto-swap: if current player IS the partner in existing match,
            # swap so partner_id points to the original player1.
            if existing_partner_match.partner_id == player_id:
                # Current player was the partner → swap: partner = original player1
                partner_id = existing_partner_match.player1_id
                partner_nombre = existing_partner_match.player1.name if existing_partner_match.player1 else existing_partner_match.partner_nombre
            else:
                partner_id = existing_partner_match.partner_id
                partner_nombre = existing_partner_match.partner_nombre

    # Verify partner_id belongs to same user
    if partner_id is not None:
        partner_player = db.query(PlayerModel).filter(
            PlayerModel.id == partner_id,
            PlayerModel.owner_id == current_user.id,
        ).first()
        if not partner_player:
            raise HTTPException(
                status_code=400,
                detail="El compañero seleccionado no existe o no pertenece a tu cuenta.",
            )
        # Auto-fill partner_nombre from player name if not provided
        if not partner_nombre:
            partner_nombre = partner_player.name

    match = MatchModel(
        player1_id=player_id,
        player2_id=player_id,       # self-reference OK — kept for backward compat
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
        played_at=datetime.combine(data.fecha_partido, datetime.utcnow().time()) if data.fecha_partido else datetime.utcnow(),
        partner_id=partner_id,
        partner_nombre=partner_nombre,
    )
    db.add(match)
    db.commit()
    db.refresh(match)

    # ── Notificar al compañero si está registrado ────────────────
    if partner_id and partner_id != player_id:
        from app.infrastructure.database.models import NotificationModel
        tipo = "torneo" if data.tournament_id else "amistoso"
        resultado = "Victoria" if data.ganado else "Derrota"
        notif = NotificationModel(
            user_id=current_user.id,
            type="match_added",
            title=f"{player.name} te ha añadido como compañero",
            message=f"{tipo.upper()} — {resultado} vs {data.rival_nombre}",
            related_url=f"/player/{player_id}",
        )
        db.add(notif)
        # Mantener solo las últimas 50 notificaciones
        all_ids = db.query(NotificationModel.id).filter(
            NotificationModel.user_id == current_user.id,
        ).order_by(NotificationModel.created_at.desc()).offset(50).all()
        if all_ids:
            db.query(NotificationModel).filter(
                NotificationModel.id.in_([r[0] for r in all_ids])
            ).delete(synchronize_session=False)
        db.commit()

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
            MatchModel.partner_id == player_id,
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

    matches = (
        query
        .options(joinedload(MatchModel.player1))
        .order_by(MatchModel.played_at.desc())
        .limit(20)
        .all()
    )
    # Hydrate player1_name for correct partner display on the other side
    result = []
    for m in matches:
        d = MatchPublicSchema.model_validate(m)
        d.player1_name = m.player1.name if m.player1 else None
        result.append(d)
    return result


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
        _player_filter(player_id),
    ).first()
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Partido no encontrado o no tenés permiso para editarlo. Solo vos o tu compañero pueden modificar este partido.",
        )

    # Verify tournament ownership if provided
    legacy_torneo = None
    if data.tournament_id is not None:
        tournament = db.query(TournamentModel).filter(
            TournamentModel.id == data.tournament_id,
        ).first()
        if not tournament:
            raise HTTPException(status_code=404, detail="Torneo no encontrado")
        legacy_torneo = tournament.name

        # Validar ronda
        if data.ronda:
            round_idx = get_round_index(data.ronda)
            if round_idx >= 0:
                # Regla 1: si hay derrota en ronda INFERIOR (o en esta misma ronda si es derrota), no se puede pasar después
                constraining_rounds = ROUND_ORDER[:round_idx + 1] if data.ganado is False else ROUND_ORDER[:round_idx]
                lower_loss = db.query(MatchModel).filter(
                    _player_filter(player_id),
                    MatchModel.tournament_id == data.tournament_id,
                    MatchModel.ganado == False,
                    MatchModel.ronda.in_(constraining_rounds),
                    MatchModel.id != match_id,
                ).first()
                if lower_loss:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Este jugador ya perdió en {lower_loss.ronda}. No puede haber partidos en rondas posteriores.",
                    )
                # Si el partido actual es derrota y se mueve a ronda superior, también bloquear
                if data.ganado is False and data.ronda != match.ronda and ROUND_ORDER.index(match.ronda) < round_idx:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Este partido es una derrota en {match.ronda}. No se puede subir a {data.ronda}.",
                    )

                # Regla 2: si se cambia a derrota, no puede haber partidos GANADOS en rondas superiores
                if data.ganado is False and data.ronda != match.ronda:
                    higher_win = db.query(MatchModel).filter(
                        _player_filter(player_id),
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

                # Regla 3: no saltar rondas — si hay otros partidos en el torneo, la ronda debe ser consecutiva
                other_exists = db.query(MatchModel).filter(
                    _player_filter(player_id),
                    MatchModel.tournament_id == data.tournament_id,
                    MatchModel.id != match_id,
                ).first()
                if other_exists and round_idx > 0 and data.ronda != match.ronda:
                    prev_round = ROUND_ORDER[round_idx - 1]
                    prev_win = db.query(MatchModel).filter(
                        _player_filter(player_id),
                        MatchModel.tournament_id == data.tournament_id,
                        MatchModel.ronda == prev_round,
                        MatchModel.ganado == True,
                        MatchModel.id != match_id,
                    ).first()
                    if not prev_win:
                        raise HTTPException(
                            status_code=400,
                            detail=f"No se puede jugar {data.ronda} sin haber ganado {prev_round} antes. Las rondas deben ser consecutivas.",
                        )

            # Regla 4: no duplicar ronda en el mismo torneo (excluyendo este partido)
            if data.ronda != match.ronda or data.tournament_id != match.tournament_id:
                existing = db.query(MatchModel).filter(
                    _player_filter(player_id),
                    MatchModel.tournament_id == data.tournament_id,
                    MatchModel.ronda == data.ronda,
                    MatchModel.id != match_id,
                ).first()
                if existing:
                    raise HTTPException(
                        status_code=400,
                        detail=f"Ya existe otro partido en {data.ronda} para este torneo.",
                    )

    # ── Partner / Compañero update logic ────────────────────────────
    if data.tournament_id is not None:
        # Tournament match: partner is locked once set on any match in this tournament.
        # Auto-swap: if current player IS the partner in existing match, swap.
        existing_partner_match = db.query(MatchModel).filter(
            _player_filter(player_id),
            MatchModel.tournament_id == data.tournament_id,
            MatchModel.partner_id.isnot(None),
            MatchModel.id != match_id,
        ).first()
        if existing_partner_match and existing_partner_match.id != match.id:
            # Preservar el compañero original del torneo, sin intercambiar roles
            match.partner_id = existing_partner_match.partner_id
            match.partner_nombre = existing_partner_match.partner_nombre
        else:
            # First tournament match without partner yet — allow setting it
            partner_id = data.partner_id
            partner_nombre = data.partner_nombre

            if partner_id is not None:
                partner_player = db.query(PlayerModel).filter(
                    PlayerModel.id == partner_id,
                    PlayerModel.owner_id == current_user.id,
                ).first()
                if not partner_player:
                    raise HTTPException(
                        status_code=400,
                        detail="El compañero seleccionado no existe o no pertenece a tu cuenta.",
                    )
                if not partner_nombre:
                    partner_nombre = partner_player.name
            match.partner_id = partner_id
            match.partner_nombre = partner_nombre
    else:
        # Amistoso: allow changing partner freely
        partner_id = data.partner_id
        partner_nombre = data.partner_nombre

        if partner_id is not None:
            partner_player = db.query(PlayerModel).filter(
                PlayerModel.id == partner_id,
                PlayerModel.owner_id == current_user.id,
            ).first()
            if not partner_player:
                raise HTTPException(
                    status_code=400,
                    detail="El compañero seleccionado no existe o no pertenece a tu cuenta.",
                )
            if not partner_nombre:
                partner_nombre = partner_player.name
        match.partner_id = partner_id
        match.partner_nombre = partner_nombre

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
    if data.notes is not None:
        match.notes = data.notes
    if data.fecha_partido is not None:
        match.played_at = datetime.combine(data.fecha_partido, match.played_at.time())

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
        _player_filter(player_id),
    ).first()
    if not match:
        raise HTTPException(
            status_code=404,
            detail="Partido no encontrado o no tenés permiso para eliminarlo. Solo vos o tu compañero pueden eliminar este partido.",
        )

    # Limpiar notificaciones relacionadas con este partido
    from app.infrastructure.database.models import NotificationModel
    notif_msg = f"/player/{player_id}"
    db.query(NotificationModel).filter(
        NotificationModel.user_id == current_user.id,
        NotificationModel.related_url == notif_msg,
    ).delete()
    db.delete(match)
    db.commit()
