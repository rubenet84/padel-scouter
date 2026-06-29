import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator
from app.domain.value_objects.category import PlayerCategory, ScoringMethod
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────────

class UserRegisterSchema(BaseModel):
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
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
    derecha:       int = Field(default=50, ge=0, le=100)
    reves:         int = Field(default=50, ge=0, le=100)
    volea_derecha: int = Field(default=50, ge=0, le=100)
    volea_reves:   int = Field(default=50, ge=0, le=100)
    bandeja:       int = Field(default=50, ge=0, le=100)
    vibora:       int = Field(default=50, ge=0, le=100)
    remate:       int = Field(default=50, ge=0, le=100)
    globo:        int = Field(default=50, ge=0, le=100)
    saque:        int = Field(default=50, ge=0, le=100)
    bajada_pared: int = Field(default=50, ge=0, le=100)
    velocidad:    int = Field(default=50, ge=0, le=100)
    resistencia:  int = Field(default=50, ge=0, le=100)
    reflejos:     int = Field(default=50, ge=0, le=100)
    tactica:            int = Field(default=50, ge=0, le=100)
    presion:            int = Field(default=50, ge=0, le=100)
    trabajo_en_pareja:  int = Field(default=50, ge=0, le=100)


class PlayerCreateSchema(BaseModel):
    name:     str = Field(min_length=2, max_length=150)
    category: PlayerCategory
    stats:    PlayerStatsSchema = PlayerStatsSchema()


class PlayerPublicSchema(BaseModel):
    id:       UUID
    name:     str
    category: PlayerCategory
    owner_id: UUID
    avatar_url: str | None = None

    derecha:       int = 50
    reves:         int = 50
    volea_derecha: int = 50
    volea_reves:   int = 50
    bandeja:       int = 50
    vibora:       int = 50
    remate:       int = 50
    globo:        int = 50
    saque:        int = 50
    bajada_pared: int = 50
    velocidad:    int = 50
    resistencia:  int = 50
    reflejos:     int = 50
    tactica:            int = 50
    presion:            int = 50
    trabajo_en_pareja:  int = 50

    model_config = {"from_attributes": True}


# ── Computed Stats ────────────────────────────────────────────

class ComputedStatsSchema(BaseModel):
    """Competitive stats computed from matches + tournaments."""

    torneos:   int
    win_rate:  float  # 0.0 – 100.0 percentage
    fep_points: int

    model_config = {"from_attributes": True}


# ── Analysis ──────────────────────────────────────────────────

class AnalysisPublicSchema(BaseModel):
    id:               UUID
    player_id:        UUID
    power_level:      int
    category:         PlayerCategory
    ai_description:   str
    strengths:        list[str]
    weaknesses:       list[str]
    improvement_plan: str
    golpe_definitivo: str | None = None
    golpe_descripcion: str | None = None
    golpe_puntuacion:  int | None = None
    nivel_amenaza:    str | None = None

    model_config = {"from_attributes": True}


# ── Matches ───────────────────────────────────────────────────

def _is_valid_set_score(a: int, b: int) -> bool:
    """Valida un set según reglamento FIP 2026."""
    high, low = max(a, b), min(a, b)
    if high == 7 and low == 5: return True   # 7-5
    if high == 7 and low == 6: return True   # 7-6 tie-break
    if high == 6 and low <= 4: return True   # 6-0 a 6-4
    return False                              # 6-5 necesita tie-break


class MatchCreateSchema(BaseModel):
    rival_nombre:   str = Field(min_length=2, max_length=150)
    resultado:      str = Field(min_length=3, max_length=50)
    ganado:         bool
    tournament_id:  UUID | None = Field(default=None, description="FK → tournaments.id. null = amistoso")
    ronda:          str | None = Field(default=None, max_length=100, description="Fase de grupos, Octavos, Cuartos, Semifinal, Final, etc.")
    scoring_method: ScoringMethod = ScoringMethod.CON_VENTAJA
    notes:          str | None = None

    @field_validator("resultado")
    @classmethod
    def validate_resultado(cls, v: str) -> str:
        """
        FIP 2026 — formato: '6-4 6-3' o '6-4 3-6 7-5'
        Sets separados por espacios. Tie-break: 7-6.
        """
        sets = v.strip().split()
        if len(sets) < 2 or len(sets) > 3:
            raise ValueError("Debe tener 2 o 3 sets (ej: '6-4 6-3' o '6-4 3-6 7-5')")
        for s in sets:
            parts = s.split('-')
            if len(parts) != 2:
                raise ValueError(f"Formato incorrecto en set: {s}")
            try:
                a, b = int(parts[0]), int(parts[1])
            except ValueError:
                raise ValueError(f"Puntuación no numérica: {s}")
            if not _is_valid_set_score(a, b):
                raise ValueError(
                    f"Set inválido según FIP 2026: {s}. "
                    f"Valores válidos: 6-0 a 6-4, 7-5, 7-6"
                )
        return v.strip()


class MatchPublicSchema(BaseModel):
    id:             UUID
    player1_id:     UUID
    rival_nombre:   str | None = None
    tournament_id:  UUID | None = None
    ronda:          str | None = None
    resultado:      str
    ganado:         bool
    scoring_method: ScoringMethod
    played_at:      datetime
    notes:          str | None = None

    model_config = {"from_attributes": True}
