"""Badges service — compute achievement badges from match history."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.infrastructure.database.models import AnalysisModel, MatchModel


def compute_player_badges(db: Session, player_id: UUID) -> list[dict]:
    """Compute all achievement badges for a player from match + analysis data."""
    matches = db.query(MatchModel).filter(
        or_(
            MatchModel.player1_id == player_id,
            MatchModel.player2_id == player_id,
            MatchModel.partner_id == player_id,
        )
    ).all()

    total = len(matches)
    wins = sum(1 for m in matches if m.ganado)
    losses = total - wins

    best_streak = 0
    s = 0
    for m in sorted(matches, key=lambda x: x.played_at or datetime.min):
        if m.ganado:
            s += 1
            best_streak = max(best_streak, s)
        else:
            s = 0

    tw = sum(
        1 for m in matches
        if m.ganado and m.tournament_id is not None
        and m.ronda and "final" in (m.ronda or "").lower()
    )

    from sqlalchemy import desc as sa_desc
    a = db.query(AnalysisModel).filter(
        AnalysisModel.player_id == player_id
    ).order_by(sa_desc(AnalysisModel.created_at)).first()

    pl = a.power_level if a else 0

    badges = []
    if total >= 1:
        badges.append({"id": "first_blood", "icon": "🩸", "label": "Primera Sangre",
                        "desc": "Primer partido jugado", "color": "#ef4444"})
    if best_streak >= 3:
        badges.append({"id": "streak", "icon": "🔥", "label": "En Racha",
                        "desc": "3 victorias seguidas", "color": "#f97316"})
    if best_streak >= 10:
        badges.append({"id": "unstoppable", "icon": "⚔️", "label": "Imparable",
                        "desc": "10 partidos sin perder", "color": "#dc2626"})
    if total >= 50:
        badges.append({"id": "veteran", "icon": "⏳", "label": "Veterano",
                        "desc": "50 partidos jugados", "color": "#8b5cf6"})
    if total >= 100:
        badges.append({"id": "century", "icon": "💯", "label": "Centenario",
                        "desc": "100 partidos jugados", "color": "#fbbf24"})
    if wins >= 3 and losses == 0:
        badges.append({"id": "invictus", "icon": "🛡️", "label": "Invicto",
                        "desc": "100% partidos ganados, mínimo 3", "color": "#06b6d4"})
    if tw >= 1:
        badges.append({"id": "champion", "icon": "🏆", "label": "Campeón",
                        "desc": "1 torneo ganado", "color": "#FFD700"})
    if tw >= 10:
        badges.append({"id": "machine", "icon": "🤖", "label": "Máquina",
                        "desc": "10 torneos ganados", "color": "#10b981"})
    if pl >= 5000:
        badges.append({"id": "power_5000", "icon": "⚡", "label": "Poderoso",
                        "desc": "Power Level ≥ 5000", "color": "#a855f7"})
    if pl >= 7500:
        badges.append({"id": "power_7500", "icon": "💥", "label": "Élite",
                        "desc": "Power Level ≥ 7500", "color": "#ec4899"})

    return badges
