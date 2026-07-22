"""
Schemas Pydantic para los endpoints de estadísticas.

Define los modelos de respuesta para ranking, top players, comparador,
H2H, récords, categorías, evolución y highlights comunitarios.

Todos los schemas usan ApiResponse como envoltorio estándar con campos
success, data y error para consistencia en la API.
"""
from uuid import UUID

from pydantic import BaseModel


class ApiResponse(BaseModel):
    """Envoltorio estándar para todas las respuestas de la API de stats."""
    success: bool = True
    data: dict | list | None = None
    error: str | None = None


class PlayerBrief(BaseModel):
    """Datos mínimos de un jugador para listados y resúmenes."""
    id: UUID
    name: str
    category: str
    points: int = 0
    win_pct: float = 0.0


class GlobalSummary(BaseModel):
    """Resumen global de la comunidad del usuario."""
    total_players: int = 0
    total_matches: int = 0
    total_tournaments: int = 0
    total_friendlies: int = 0
    total_sets: int = 0
    total_games: int = 0
    ranking_leader: PlayerBrief | None = None
    best_win_pct: PlayerBrief | None = None


class PlayerRankRow(BaseModel):
    """Fila individual en el ranking."""
    position: int = 0
    id: UUID
    name: str
    category: str
    points: int = 0
    wins: int = 0
    losses: int = 0
    matches: int = 0
    win_pct: float = 0.0
    sets_won: int = 0
    games_won: int = 0
    streak: int = 0  # positive = win streak, negative = loss streak


class RankingResponse(BaseModel):
    """Respuesta paginada del ranking."""
    players: list[PlayerRankRow]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── PR #3: Top Players ──────────────────────────────────────────────


class TopPlayerEntry(BaseModel):
    """Entrada en una lista de top jugadores."""
    player_id: UUID
    name: str
    category: str
    value: float | int  # the metric value


class TopLists(BaseModel):
    """10 listas de top 5 jugadores por distintas métricas."""
    top_points: list[TopPlayerEntry] = []
    top_wins: list[TopPlayerEntry] = []
    top_win_pct: list[TopPlayerEntry] = []
    top_matches: list[TopPlayerEntry] = []
    top_tournaments_won: list[TopPlayerEntry] = []
    top_finals: list[TopPlayerEntry] = []
    top_semis: list[TopPlayerEntry] = []
    top_sets_won: list[TopPlayerEntry] = []
    top_games_won: list[TopPlayerEntry] = []
    top_streak: list[TopPlayerEntry] = []


# ── PR #3: Comparador ──────────────────────────────────────────────


class ComparisonPlayer(BaseModel):
    """Datos de un jugador en una comparación lado a lado."""
    id: UUID
    name: str
    category: str
    avatar: str | None = None
    position: int | None = None   # posición en el ranking de su categoría
    points: int = 0
    matches: int = 0
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    sets_won: int = 0
    games_won: int = 0
    streak: int = 0


class ComparisonResult(BaseModel):
    """Resultado de comparación entre dos jugadores."""
    player_a: ComparisonPlayer
    player_b: ComparisonPlayer
    same_category: bool = True
    category_name: str | None = None
    point_difference: int | None = None
    notice: str | None = None  # mensaje si no son de la misma categoría


# ── PR #3: H2H ─────────────────────────────────────────────────────


class H2HMatch(BaseModel):
    """Partido individual en el historial H2H."""
    date: str | None = None
    winner_id: UUID | None = None
    winner_name: str | None = None
    sets_p1: int = 0
    sets_p2: int = 0
    games_p1: int = 0
    games_p2: int = 0
    resultado: str | None = None


class H2HResult(BaseModel):
    """Historial completo de enfrentamientos entre dos jugadores."""
    player_a_id: UUID
    player_b_id: UUID
    total_matches: int = 0
    wins_a: int = 0
    wins_b: int = 0
    sets_a: int = 0
    sets_b: int = 0
    games_a: int = 0
    games_b: int = 0
    last_match: H2HMatch | None = None
    history: list[H2HMatch] = []


# ── PR #4: Records, Categories, Evolution, Community ──────────────


class PlayerRecord(BaseModel):
    """Récord individual para una métrica específica."""
    player_id: UUID
    name: str
    category: str
    value: float | int
    metric_key: str    # e.g. "points", "wins", "streak"
    metric_label: str  # e.g. "Puntos FEP", "Victorias"


class CategoryDetail(BaseModel):
    """Estadísticas agregadas de una categoría."""
    category: str
    total_players: int = 0
    total_matches: int = 0
    total_wins: int = 0
    total_losses: int = 0
    avg_win_pct: float = 0.0
    avg_points: float = 0.0
    leader_name: str | None = None
    leader_points: int | None = None
    top_players: list[TopPlayerEntry] = []


class EvolutionEntry(BaseModel):
    """Evolución de puntos de un jugador (sparkline)."""
    player_id: UUID
    name: str
    category: str
    current_points: int = 0
    sparkline: list[int] = []  # historical points — placeholder for now


class CommunityHighlights(BaseModel):
    """Highlights del dashboard comunitario."""
    most_points: PlayerBrief | None = None
    best_form: PlayerBrief | None = None
    best_pair: dict | None = None  # {player1_name, player2_name, win_pct, matches}
    most_active: PlayerBrief | None = None
