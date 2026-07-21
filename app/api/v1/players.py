import logging
from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import StreamingResponse, Response
from datetime import datetime, timezone

logger = logging.getLogger(__name__)
from sqlalchemy import or_, text
from sqlalchemy.orm import Session, joinedload

from app.core.dependencies import get_current_user, _optional_auth
from app.infrastructure.database.session import get_db
from sqlalchemy import func, desc as sa_desc
from app.infrastructure.database.models import PlayerModel, UserModel, MatchModel, TournamentModel, AnalysisModel
from app.schemas.player import (
    PlayerCreateSchema, PlayerPublicSchema,
    MatchCreateSchema, MatchPublicSchema,
    ComputedStatsSchema, PlayerAnalyticsSchema,
)


from app.domain.value_objects.rounds import ROUND_ORDER, get_round_index
from app.services.computed_stats_service import get_computed_stats
from app.services.badges_service import compute_player_badges
from app.services.avatar_service import process_avatar

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
        mano=data.mano,
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
        PlayerModel.owner_id == current_user.id,
        PlayerModel.is_deleted == False,
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


@router.get("/{player_id}/badges")
def get_player_badges(
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
    return compute_player_badges(db, player_id)


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
    player.mano     = data.mano
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


@router.get("/{player_id}/evolution")
def get_player_evolution(
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
        or_(MatchModel.player1_id == player_id, MatchModel.player2_id == player_id, MatchModel.partner_id == player_id),
        MatchModel.played_at.isnot(None),
    ).order_by(MatchModel.played_at.asc()).all()

    from collections import defaultdict
    fep_by_date = defaultdict(int)
    for m in matches:
        if not m.played_at: continue
        fep = 0
        if m.tournament_id and m.tournament: fep = m.tournament.fep_points or 0
        fep_by_date[m.played_at.strftime("%Y-%m-%d")] += fep
    points_timeline = []
    cumulative = 0
    for d in sorted(fep_by_date): cumulative += fep_by_date[d]; points_timeline.append({"date": d, "points": cumulative})

    monthly = defaultdict(lambda: {"wins": 0, "losses": 0})
    for m in matches:
        if not m.played_at: continue
        month_key = m.played_at.strftime("%Y-%m")
        if m.ganado: monthly[month_key]["wins"] += 1
        else: monthly[month_key]["losses"] += 1
    wins_losses = [{"month": k, "wins": v["wins"], "losses": v["losses"]} for k, v in sorted(monthly.items())]

    return {"points_timeline": points_timeline, "wins_losses_monthly": wins_losses}


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

    from app.services.analytics_service import get_match_analytics
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

    # Read file contents
    file.file.seek(0)
    contents = file.file.read()

    # Process avatar via service (validation + re-encode + save + cleanup)
    try:
        avatar_url = process_avatar(contents, file.filename or "", player.avatar_url)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # Save to DB
    player.avatar_url = avatar_url
    db.commit()
    db.refresh(player)

    return player


@router.delete("/{player_id}", status_code=200)
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
    player.is_deleted = True
    player.deleted_at = datetime.now(timezone.utc)
    db.commit()
    return {"success": True, "message": f"Jugador '{player.name}' eliminado"}


@router.put("/{player_id}/restore", status_code=200)
def restore_player(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
        PlayerModel.is_deleted == True,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado o no está eliminado")
    player.is_deleted = False
    player.deleted_at = None
    db.commit()
    return {"success": True, "message": f"Jugador '{player.name}' recuperado"}


@router.post("/{player_id}/pdf-token")
def request_pdf_download_token(
    player_id: UUID,
    db: Session = Depends(get_db),
    current_user: UserModel = Depends(get_current_user),
):
    """Generate a short-lived download token for PDF export."""
    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")
    from app.core.security import create_download_token
    token = create_download_token(str(current_user.id), str(player_id))
    return {"download_token": token, "expires_in": 300}


@router.get("/{player_id}/pdf")
def export_player_pdf_weasy(
    player_id: UUID,
    download_token: str | None = Query(None),
    db: Session = Depends(get_db),
    current_user: UserModel | None = Depends(_optional_auth),
):
    # Accept Bearer token (API client) OR short-lived download_token
    if current_user is None and download_token:
        from app.core.security import decode_download_token
        from jose import JWTError
        try:
            payload = decode_download_token(download_token)
            uid = UUID(payload.get("sub"))
            pid = UUID(payload.get("player_id"))
            if pid != player_id:
                raise HTTPException(status_code=403, detail="Token no válido para este jugador")
        except (JWTError, ValueError):
            raise HTTPException(status_code=401, detail="Token inválido o expirado")
        current_user = db.query(UserModel).filter(UserModel.id == uid).first()
        if not current_user:
            raise HTTPException(status_code=401, detail="Usuario no encontrado")
    elif current_user is None:
        raise HTTPException(status_code=401, detail="Autenticación requerida")

    player = db.query(PlayerModel).filter(
        PlayerModel.id == player_id,
        PlayerModel.owner_id == current_user.id,
    ).first()
    if not player:
        raise HTTPException(status_code=404, detail="Jugador no encontrado")

    analysis = db.query(AnalysisModel).filter(
        AnalysisModel.player_id == player_id,
    ).order_by(sa_desc(AnalysisModel.created_at)).first()

    import json
    player_dict = {c.name: getattr(player, c.name) for c in player.__table__.columns}
    player_dict["category"] = player.category.value if hasattr(player.category, "value") else str(player.category)

    # Calcular datos de matches para el PDF
    matches = db.query(MatchModel).options(joinedload(MatchModel.tournament)).filter(
        or_(MatchModel.player1_id == player_id, MatchModel.player2_id == player_id, MatchModel.partner_id == player_id)
    ).all()
    total_matches = len(matches)
    wins = sum(1 for m in matches if m.ganado)
    tourney_count = len(set(m.tournament_id for m in matches if m.tournament_id))
    win_rate = f"{round((wins / total_matches) * 100)}%" if total_matches > 0 else "—"

    # FEP usando la misma query que el player detail
    from app.domain.value_objects.fep import compute_fep_points
    fep_rows = db.execute(text("""
        SELECT m.id, m.player1_id, m.partner_id, m.ronda, m.ganado,
               m.tournament_id, t.fep_points
        FROM matches m
        LEFT JOIN tournaments t ON m.tournament_id = t.id
        WHERE m.player1_id = :pid OR m.partner_id = :pid
    """), {"pid": player_id}).fetchall()
    fep_map_dict = compute_fep_points(fep_rows, [player_id])
    fep_points_total = fep_map_dict.get(player_id, 0)

    player_dict["torneos_jugados"] = tourney_count
    player_dict["victorias"] = wins
    player_dict["win_rate"] = win_rate
    player_dict["puntos_ranking_fep"] = fep_points_total

    analysis_dict = {}
    if analysis:
        analysis_dict = {
            "power_level": analysis.power_level,
            "ai_description": analysis.ai_description or "",
            "improvement_plan": analysis.improvement_plan or "",
            "strengths": json.loads(analysis.strengths) if isinstance(analysis.strengths, str) else (analysis.strengths or []),
            "weaknesses": json.loads(analysis.weaknesses) if isinstance(analysis.weaknesses, str) else (analysis.weaknesses or []),
        }

    from app.infrastructure.pdf.generate_pdf import generate_player_pdf
    pdf_bytes = generate_player_pdf(player_dict, analysis_dict)
    filename = f"informe_{player.name.replace(' ','_')}.pdf"
    return Response(pdf_bytes, media_type="application/pdf",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'})


# ── Matches ───────────────────────────────────────────────────


def _validate_tournament_round(
    db: Session,
    player_id: UUID,
    data: MatchCreateSchema,
    *,
    exclude_match_id: UUID | None = None,
):
    """Shared round validation for add_match and update_match."""
    if not data.ronda or data.tournament_id is None:
        return

    round_idx = get_round_index(data.ronda)
    if round_idx < 0:
        raise HTTPException(
            status_code=400,
            detail=f"Ronda inválida: '{data.ronda}'. Las rondas válidas son: {', '.join(ROUND_ORDER)}",
        )

    # ── Build base filter (exclude current match for updates)
    base = [_player_filter(player_id), MatchModel.tournament_id == data.tournament_id]
    if exclude_match_id is not None:
        base.append(MatchModel.id != exclude_match_id)

    # Rule 1: if there's a loss in a LOWER round, can't play later
    loss_below = ROUND_ORDER[:round_idx + 1] if data.ganado is False else ROUND_ORDER[:round_idx]
    lower_loss = db.query(MatchModel).filter(
        *base,
        MatchModel.ganado == False,
        MatchModel.ronda.in_(loss_below),
    ).first()
    if lower_loss:
        raise HTTPException(
            status_code=400,
            detail=f"Este jugador ya perdió en {lower_loss.ronda}. No puede haber partidos en rondas posteriores.",
        )

    # Rule 2: if marking as loss, can't have WINS in higher rounds
    if data.ganado is False:
        higher_win = db.query(MatchModel).filter(
            *base,
            MatchModel.ganado == True,
            MatchModel.ronda.in_(ROUND_ORDER[round_idx + 1:]),
        ).first()
        if higher_win:
            raise HTTPException(
                status_code=400,
                detail="No se puede marcar como derrota porque hay partidos ganados en rondas superiores. Eliminá primero esos partidos.",
            )

    # Rule 3: no skipping rounds — must be consecutive
    existing_any = db.query(MatchModel).filter(*base).first()
    if existing_any and round_idx > 0:
        prev_round = ROUND_ORDER[round_idx - 1]
        prev_win = db.query(MatchModel).filter(
            *base,
            MatchModel.ronda == prev_round,
            MatchModel.ganado == True,
        ).first()
        if not prev_win:
            raise HTTPException(
                status_code=400,
                detail=f"No se puede jugar {data.ronda} sin haber ganado {prev_round} antes. Las rondas deben ser consecutivas.",
            )

    # Rule 4: no duplicate round in the same tournament
    existing = db.query(MatchModel).filter(
        *base,
        MatchModel.ronda == data.ronda,
    ).first()
    if existing:
        raise HTTPException(
            status_code=400,
            detail=f"Ya existe un partido en {data.ronda} para este torneo. Solo se puede editar o eliminar.",
        )


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

        _validate_tournament_round(db, player_id, data)

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
        rivalText = data.rival_nombre or "Rival"
        safeRival = rivalText.replace('&','&amp;').replace('<','&lt;').replace('>','&gt;')
        fechaStr = match.played_at.strftime('%d/%m/%Y') if match.played_at else ''
        tipoBadge = '<span style="background:rgba(255,215,0,0.1);color:#FFD700;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;text-transform:uppercase;">TORNEO</span>' if data.tournament_id else '<span style="background:rgba(255,107,0,0.1);color:#FF6B00;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;text-transform:uppercase;">AMISTOSO</span>'
        resultBadge = '<span style="background:rgba(0,255,135,0.1);color:#00FF87;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;text-transform:uppercase;">VICTORIA</span>' if data.ganado else '<span style="background:rgba(255,45,45,0.1);color:#FF2D2D;padding:2px 6px;border-radius:4px;font-size:10px;font-weight:bold;text-transform:uppercase;">DERROTA</span>'
        notif = NotificationModel(
            user_id=current_user.id,
            player_id=partner_id,
            match_id=match.id,
            type="match_added",
            title=f"{player.name} te ha añadido como compañero",
            message=f"{tipoBadge} — {resultBadge} vs <span style=\"color:white;\">{safeRival}</span>  {data.resultado or ''}  <span style=\"color:#fbbf24;font-size:9px;\">{fechaStr}</span>",
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

        _validate_tournament_round(db, player_id, data, exclude_match_id=match_id)

        # Update-specific: no mover una derrota a ronda superior
        if data.ronda and data.ganado is False and data.ronda != match.ronda \
                and ROUND_ORDER.index(match.ronda) < get_round_index(data.ronda):
            raise HTTPException(
                status_code=400,
                detail=f"Este partido es una derrota en {match.ronda}. No se puede subir a {data.ronda}.",
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

    # Limpiar notificaciones de este partido específico
    from app.infrastructure.database.models import NotificationModel
    db.query(NotificationModel).filter(
        NotificationModel.match_id == match_id,
    ).delete()
    db.delete(match)
    db.commit()

