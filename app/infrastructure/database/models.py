from datetime import datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Column, String, Integer, Float, Boolean,
    Date, DateTime, ForeignKey, Enum as SAEnum, Text
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import DeclarativeBase, relationship

from app.domain.value_objects.category import PlayerCategory, ScoringMethod

UTC = timezone.utc

class Base(DeclarativeBase):
    pass


class UserModel(Base):
    __tablename__ = "users"

    id           = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    email        = Column(String(255), unique=True, nullable=False, index=True)
    username     = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    role         = Column(String(20), default="viewer", nullable=False)
    is_active    = Column(Boolean, default=True, nullable=False)
    created_at   = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    players    = relationship("PlayerModel", back_populates="owner")


class PlayerModel(Base):
    __tablename__ = "players"

    id       = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name     = Column(String(150), nullable=False)
    category = Column(SAEnum(PlayerCategory), nullable=False)
    owner_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    updated_at = Column(DateTime, default=lambda: datetime.now(UTC), onupdate=lambda: datetime.now(UTC))

    # Stats técnica
    derecha       = Column(Integer, default=50)
    reves         = Column(Integer, default=50)
    volea         = Column(Integer, default=50)       # legacy — mantener para compat
    volea_derecha = Column(Integer, default=50)
    volea_reves   = Column(Integer, default=50)
    bandeja       = Column(Integer, default=50)
    vibora       = Column(Integer, default=50)
    smash        = Column(Integer, default=50)    # legacy
    remate       = Column(Integer, default=50)
    lob          = Column(Integer, default=50)    # legacy
    globo        = Column(Integer, default=50)
    saque        = Column(Integer, default=50)
    bajada_pared = Column(Integer, default=50)

    # Stats físico
    velocidad    = Column(Integer, default=50)
    resistencia  = Column(Integer, default=50)
    reflejos     = Column(Integer, default=50)

    # Stats mental
    tactica            = Column(Integer, default=50)
    presion            = Column(Integer, default=50)
    trabajo_en_pareja  = Column(Integer, default=50)

    # Avatar
    avatar_url = Column(String(500), nullable=True)

    owner     = relationship("UserModel", back_populates="players")
    analyses  = relationship("AnalysisModel", back_populates="player")
    matches_as_p1 = relationship("MatchModel", foreign_keys="MatchModel.player1_id")
    matches_as_p2 = relationship("MatchModel", foreign_keys="MatchModel.player2_id")


class TournamentModel(Base):
    __tablename__ = "tournaments"

    id         = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    name       = Column(String(200), nullable=False)
    date       = Column(Date, nullable=False)
    fep_points = Column(Integer, default=0, nullable=True)
    owner_id   = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    player_id  = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)
    created_at = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    owner   = relationship("UserModel")
    player  = relationship("PlayerModel")
    matches = relationship("MatchModel", back_populates="tournament")


class AnalysisModel(Base):
    __tablename__ = "analyses"

    id               = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    player_id        = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    power_level      = Column(Integer, nullable=False)
    category         = Column(SAEnum(PlayerCategory), nullable=False)
    ai_description   = Column(Text, nullable=False)
    strengths        = Column(Text, nullable=False)   # JSON string
    weaknesses       = Column(Text, nullable=False)   # JSON string
    improvement_plan = Column(Text, nullable=False)
    golpe_definitivo = Column(Text, nullable=True)
    golpe_descripcion = Column(Text, nullable=True)
    golpe_puntuacion  = Column(Integer, nullable=True)
    nivel_amenaza    = Column(String(20), nullable=True)
    created_at       = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)

    player = relationship("PlayerModel", back_populates="analyses")


class MatchModel(Base):
    __tablename__ = "matches"

    id             = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    player1_id     = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    player2_id     = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=False)
    rival_nombre   = Column(String(150), nullable=True)
    torneo         = Column(String(150), nullable=True)
    tournament_id  = Column(UUID(as_uuid=True), ForeignKey("tournaments.id"), nullable=True)
    ronda          = Column(String(100), nullable=True)
    resultado      = Column(String(50),  nullable=True)
    ganado         = Column(Boolean,     default=True, nullable=False)
    scoring_method = Column(SAEnum(ScoringMethod), nullable=False,
                            default=ScoringMethod.CON_VENTAJA)
    result         = Column(String(50),  nullable=False)
    winner_id      = Column(UUID(as_uuid=True), ForeignKey("players.id"), nullable=True)
    played_at      = Column(DateTime, default=lambda: datetime.now(UTC), nullable=False)
    notes          = Column(Text, nullable=True)

    tournament = relationship("TournamentModel", back_populates="matches")