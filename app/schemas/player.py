"""
Schemas Pydantic para la API de jugadores, autenticación y partidos.

Define los contratos de entrada/salida de la API REST:
- Auth: registro, login, tokens.
- Players: creación, lectura, estadísticas.
- Matches: creación, validación FIP 2026.
- Analysis: resultado de análisis IA.

Las validaciones de contraseña y formato de resultado implementan
reglas de seguridad (OWASP A02) y reglamento FIP.
"""
import re
from uuid import UUID
from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator
from app.domain.value_objects.category import PlayerCategory, ScoringMethod
from datetime import date, datetime


# ── Auth ──────────────────────────────────────────────────────

class UserRegisterSchema(BaseModel):
    """Schema de registro de usuario con validación de contraseña fuerte."""
    email: EmailStr
    username: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """OWASP A02: valida complejidad mínima de contraseña.

        Requisitos:
        - Mínimo 12 caracteres.
        - Al menos una mayúscula, una minúscula, un número y un carácter especial.
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
        """Normaliza el email a minúsculas y sin espacios."""
        return v.lower().strip()


class UserLoginSchema(BaseModel):
    """Schema de login: solo email y contraseña."""
    email: EmailStr
    password: str

    @field_validator("email")
    @classmethod
    def normalize_email(cls, v: str) -> str:
        return v.lower().strip()


class TokenSchema(BaseModel):
    """Tokens JWT devueltos tras login/refresh."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class UserPublicSchema(BaseModel):
    """Datos públicos del usuario (sin contraseña ni datos sensibles)."""
    id: UUID
    email: str
    username: str
    role: str

    model_config = {"from_attributes": True}


# ── Players ───────────────────────────────────────────────────

class PlayerStatsSchema(BaseModel):
    """Estadísticas base del jugador, todas en rango 0-100."""
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
    """Datos necesarios para crear un jugador."""
    name:     str = Field(min_length=2, max_length=150)
    category: PlayerCategory
    stats:    PlayerStatsSchema = PlayerStatsSchema()
    mano:     str = "Derecha"


class PlayerPublicSchema(BaseModel):
    """Representación pública de un jugador, incluye stats y power_level."""
    id:       UUID
    name:     str
    category: PlayerCategory
    owner_id: UUID
    avatar_url: str | None = None
    power_level: int | None = None
    mano: str = "Derecha"

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

    is_deleted: bool = False
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


# ── Computed Stats ────────────────────────────────────────────

class ComputedStatsSchema(BaseModel):
    """Estadísticas competitivas computadas desde partidos + torneos."""

    torneos:   int
    win_rate:  float  # 0.0 – 100.0 percentage
    fep_points: int

    model_config = {"from_attributes": True}


# ── Match Analytics ────────────────────────────────────────────

class PlayerAnalyticsSchema(BaseModel):
    """Estadísticas detalladas basadas en partidos y torneos reales."""

    total_partidos:    int
    victorias:         int
    derrotas:          int
    win_rate:          float          # 0.0 – 100.0
    total_sets:        int
    sets_ganados:      int
    sets_perdidos:     int
    set_ratio:         float          # 0.0 – 1.0
    sets_por_partido:  float
    partidos_2_sets:   int
    partidos_3_sets:   int
    torneos_jugados:   int
    amistosos_jugados: int
    mejor_ronda:       str | None
    rondas_breakdown:  dict[str, int]
    fase_media_nombre: str | None
    fase_media_idx:    float
    scoring_breakdown: dict[str, int]


# ── Analysis ──────────────────────────────────────────────────

class AnalysisPublicSchema(BaseModel):
    """Resultado de un análisis IA para consulta pública."""
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
    """Valida un resultado de set según reglas FIP 2026.

    Resultados válidos:
    - 6-0, 6-1, 6-2, 6-3, 6-4
    - 7-5, 7-6 (tie-break)
    """
    if a < 0 or b < 0:
        return False
    high, low = max(a, b), min(a, b)
    if high == 7 and (low == 5 or low == 6):
        return True  # 7-5 o 7-6 tie-break
    if high == 6 and low <= 4:
        return True  # 6-0 a 6-4
    return False


def _has_lesion_notes(notes: str | None) -> bool:
    """Detecta si las notas indican lesión/retiro/abandono.

    Si es así, se saltea la validación estricta de scores porque
    los sets pueden ser parciales (ej: 6-2 3-0 ret.).
    """
    if not notes:
        return False
    return bool(re.search(r'lesi[oó]n|retiro|retirada|abandono', notes, re.IGNORECASE))


class MatchCreateSchema(BaseModel):
    """Schema para crear/actualizar un partido."""
    rival_nombre:   str = Field(min_length=2, max_length=150)
    resultado:      str = Field(min_length=3, max_length=50)
    ganado:         bool
    tournament_id:  UUID | None = Field(default=None, description="FK → tournaments.id. null = amistoso")
    ronda:          str | None = Field(default=None, max_length=100, description="Fase de grupos, Octavos, Cuartos, Semifinal, Final, etc.")
    partner_id:     UUID | None = Field(default=None, description="FK → players.id del compañero")
    partner_nombre: str | None = Field(default=None, max_length=150, description="Nombre libre del compañero (cuando no está registrado)")
    scoring_method: ScoringMethod = ScoringMethod.CON_VENTAJA
    notes:          str | None = None
    fecha_partido:  date | None = Field(default=None, description="Fecha en que se jugó el partido. Si no se envía, se usa la fecha actual.")

    @field_validator("fecha_partido")
    @classmethod
    def validate_fecha_not_future(cls, v: date | None) -> date | None:
        """Bloquea fechas futuras — un partido no puede registrarse antes de jugarse."""
        if v is not None and v > date.today():
            def _ddmm(d: date) -> str:
                return f"{d.day:02d}-{d.month:02d}-{d.year}"
            raise ValueError(
                f"La fecha del partido ({_ddmm(v)}) no puede ser posterior a "
                f"hoy ({_ddmm(date.today())}). Corregí la fecha para continuar."
            )
        return v

    @field_validator("resultado")
    @classmethod
    def validate_resultado_format(cls, v: str) -> str:
        """Validación básica: formato numérico y cantidad de sets (2 o 3)."""
        v = v.strip()
        sets = v.split()
        if len(sets) < 2 or len(sets) > 3:
            raise ValueError("Debe tener 2 o 3 sets (ej: '6-4 6-3' o '6-4 3-6 7-5')")
        for s in sets:
            parts = s.split('-')
            if len(parts) != 2:
                raise ValueError(f"Formato incorrecto en set: {s}")
            try:
                int(parts[0]), int(parts[1])
            except ValueError:
                raise ValueError(f"Puntuación no numérica: {s}")
        return v

    @model_validator(mode="after")
    def validate_resultado_scores(self):
        """Valida sets según reglamento FIP 2026, salvo si hay lesión/retiro."""
        if _has_lesion_notes(self.notes):
            return self
        for s in self.resultado.split():
            a_str, b_str = s.split('-')
            a, b = int(a_str), int(b_str)
            if not _is_valid_set_score(a, b):
                raise ValueError(
                    f"Set inválido según FIP 2026: {s}. "
                    f"Valores válidos: 6-0 a 6-4, 7-5, 7-6"
                )
        return self


class MatchPublicSchema(BaseModel):
    """Representación pública de un partido."""
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
    partner_id:     UUID | None = None
    partner_nombre: str | None = None
    player1_name:   str | None = None

    model_config = {"from_attributes": True}
