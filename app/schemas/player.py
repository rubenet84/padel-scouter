from uuid import UUID
from pydantic import BaseModel, EmailStr, Field
from app.domain.value_objects.category import PlayerCategory, ScoringMethod


# ── Auth ──────────────────────────────────────────────────────

class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=100)


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str


class TokenSchema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublicSchema(BaseModel):
    id: UUID
    email: str
    username: str
    role: str

    model_config = {"from_attributes": True}


# ── Players ───────────────────────────────────────────────────

class PlayerStatsSchema(BaseModel):
    derecha:      int = Field(default=50, ge=0, le=100)
    reves:        int = Field(default=50, ge=0, le=100)
    volea:        int = Field(default=50, ge=0, le=100)
    bandeja:      int = Field(default=50, ge=0, le=100)
    vibora:       int = Field(default=50, ge=0, le=100)
    smash:        int = Field(default=50, ge=0, le=100)
    lob:          int = Field(default=50, ge=0, le=100)
    saque:        int = Field(default=50, ge=0, le=100)
    bajada_pared: int = Field(default=50, ge=0, le=100)
    velocidad:    int = Field(default=50, ge=0, le=100)
    resistencia:  int = Field(default=50, ge=0, le=100)
    reflejos:     int = Field(default=50, ge=0, le=100)
    tactica:           int = Field(default=50, ge=0, le=100)
    presion:           int = Field(default=50, ge=0, le=100)
    trabajo_en_pareja: int = Field(default=50, ge=0, le=100)
    torneos_jugados:   int = Field(default=0, ge=0)
    victorias:         int = Field(default=0, ge=0)
    puntos_ranking_fep: int = Field(default=0, ge=0)


class PlayerCreateSchema(BaseModel):
    name: str = Field(min_length=2, max_length=150)
    category: PlayerCategory
    stats: PlayerStatsSchema = PlayerStatsSchema()


class PlayerPublicSchema(BaseModel):
    id: UUID
    name: str
    category: PlayerCategory
    owner_id: UUID

    model_config = {"from_attributes": True}


# ── Analysis ──────────────────────────────────────────────────

class AnalysisPublicSchema(BaseModel):
    id: UUID
    player_id: UUID
    power_level: int
    category: PlayerCategory
    ai_description: str
    strengths: list[str]
    weaknesses: list[str]
    improvement_plan: str

    model_config = {"from_attributes": True}


# ── Matches ───────────────────────────────────────────────────

class MatchCreateSchema(BaseModel):
    player1_id: UUID
    player2_id: UUID
    scoring_method: ScoringMethod = ScoringMethod.CON_VENTAJA
    result: str = Field(min_length=3, max_length=50)  # "6-3 6-4"
    winner_id: UUID | None = None
    notes: str | None = None


class MatchPublicSchema(BaseModel):
    id: UUID
    player1_id: UUID
    player2_id: UUID
    scoring_method: ScoringMethod
    result: str
    winner_id: UUID | None

    model_config = {"from_attributes": True}