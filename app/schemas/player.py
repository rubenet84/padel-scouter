import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.domain.value_objects.category import PlayerCategory, ScoringMethod


# ── Auth ──────────────────────────────────────────────────────

class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """
        OWASP A07 — contraseña fuerte obligatoria:
        - Mínimo 12 caracteres
        - Al menos una mayúscula
        - Al menos una minúscula
        - Al menos un número
        - Al menos un carácter especial
        """
        errors = []
        if len(v) < 12:
            errors.append("mínimo 12 caracteres")
        if not re.search(r"[A-Z]", v):
            errors.append("al menos una mayúscula")
        if not re.search(r"[a-z]", v):
            errors.append("al menos una minúscula")
        if not re.search(r"\d", v):
            errors.append("al menos un número")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>_\-]", v):
            errors.append("al menos un carácter especial (!@#$%...)")
        if errors:
            raise ValueError(f"Contraseña débil: {', '.join(errors)}")
        return v

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class UserLoginSchema(BaseModel):
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


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
    result: str = Field(min_length=3, max_length=50)
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