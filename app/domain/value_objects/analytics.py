"""Match analytics computed from real match + tournament data."""

from collections import defaultdict
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.domain.value_objects.rounds import ROUND_ORDER, best_round_info
from app.infrastructure.database.models import MatchModel


def get_match_analytics(db: Session, player_id: UUID) -> dict:
    """
    Computa estadísticas detalladas basadas en partidos reales.

    Returns
    -------
    dict con claves:
        total_partidos, victorias, derrotas, win_rate,
        total_sets, sets_ganados, sets_perdidos, set_ratio, sets_por_partido,
        torneos_jugados, amistosos_jugados,
        mejor_ronda, rondas_breakdown, fase_media_nombre, fase_media_idx,
        scoring_breakdown
    """
    matches = (
        db.query(MatchModel)
        .filter(
            or_(
                MatchModel.player1_id == player_id,
                MatchModel.player2_id == player_id,
                MatchModel.partner_id == player_id,
            )
        )
        .all()
    )

    total_partidos = len(matches)

    # ── Victorias / Derrotas ──
    victorias = sum(1 for m in matches if m.ganado)
    derrotas = total_partidos - victorias
    win_rate = round(victorias / total_partidos * 100, 1) if total_partidos else 0.0

    # ── Sets ──
    total_sets = 0
    sets_ganados = 0
    sets_perdidos = 0

    for m in matches:
        if not m.resultado:
            continue
        sets = m.resultado.split()
        for s in sets:
            parts = s.split("-")
            if len(parts) != 2:
                continue
            try:
                ps, rs = int(parts[0]), int(parts[1])
                total_sets += 1
                if ps > rs:
                    sets_ganados += 1
                elif ps < rs:
                    sets_perdidos += 1
                # empate no debería ocurrir en pádel
            except ValueError:
                continue

    set_ratio = round(sets_ganados / total_sets, 3) if total_sets else 0.0
    sets_por_partido = round(total_sets / total_partidos, 1) if total_partidos else 0.0

    # ── Partidos a 2 / 3 sets ──
    partidos_2_sets = 0
    partidos_3_sets = 0
    for m in matches:
        if not m.resultado:
            continue
        n_sets = len(m.resultado.split())
        if n_sets == 2:
            partidos_2_sets += 1
        elif n_sets >= 3:
            partidos_3_sets += 1

    # ── Torneos / Amistosos ──
    tour_groups: dict[UUID | None, list[MatchModel]] = defaultdict(list)
    for m in matches:
        tour_groups[m.tournament_id].append(m)

    torneos_jugados = sum(1 for tid in tour_groups if tid is not None)
    amistosos_jugados = len(tour_groups.get(None, []))

    # ── Rondas ──
    mejor_ronda: str | None = None
    mejor_idx = -1
    round_counts: dict[str, int] = {}
    best_indices: list[int] = []

    for tid, tmatches in tour_groups.items():
        if tid is None:
            continue  # amistoso
        r_name, r_idx, _ = best_round_info(tmatches)
        if r_name is None:
            continue
        round_counts[r_name] = round_counts.get(r_name, 0) + 1
        best_indices.append(r_idx)
        if r_idx > mejor_idx:
            mejor_idx = r_idx
            mejor_ronda = r_name

    # Ordenar breakdown por índice de ronda
    rondas_breakdown = dict(
        sorted(round_counts.items(), key=lambda kv: ROUND_ORDER.index(kv[0]))
    )

    # Fase media
    fase_media_idx = round(sum(best_indices) / len(best_indices), 1) if best_indices else 0.0
    if best_indices:
        clamped = min(max(round(fase_media_idx), 0), len(ROUND_ORDER) - 1)
        fase_media_nombre = ROUND_ORDER[clamped]
    else:
        fase_media_nombre = None

    # ── Scoring breakdown ──
    scoring: dict[str, int] = {}
    for m in matches:
        sm = m.scoring_method.value if hasattr(m.scoring_method, "value") else str(m.scoring_method)
        scoring[sm] = scoring.get(sm, 0) + 1

    labels = {"con_ventaja": "Con Ventaja", "star_point": "Star Point", "punto_oro": "Punto Oro"}
    scoring_breakdown = {labels.get(k, k): v for k, v in scoring.items()}

    return {
        "total_partidos": total_partidos,
        "victorias": victorias,
        "derrotas": derrotas,
        "win_rate": win_rate,
        "total_sets": total_sets,
        "sets_ganados": sets_ganados,
        "sets_perdidos": sets_perdidos,
        "set_ratio": set_ratio,
        "sets_por_partido": sets_por_partido,
        "partidos_2_sets": partidos_2_sets,
        "partidos_3_sets": partidos_3_sets,
        "torneos_jugados": torneos_jugados,
        "amistosos_jugados": amistosos_jugados,
        "mejor_ronda": mejor_ronda,
        "rondas_breakdown": rondas_breakdown,
        "fase_media_nombre": fase_media_nombre,
        "fase_media_idx": fase_media_idx,
        "scoring_breakdown": scoring_breakdown,
    }
