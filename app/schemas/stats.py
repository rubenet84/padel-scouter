from uuid import UUID

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    data: dict | list | None = None
    error: str | None = None


class PlayerBrief(BaseModel):
    id: UUID
    name: str
    category: str
    points: int = 0
    win_pct: float = 0.0


class GlobalSummary(BaseModel):
    total_players: int = 0
    total_matches: int = 0
    total_tournaments: int = 0
    total_friendlies: int = 0
    total_sets: int = 0
    total_games: int = 0
    ranking_leader: PlayerBrief | None = None
    best_win_pct: PlayerBrief | None = None


class PlayerRankRow(BaseModel):
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
    players: list[PlayerRankRow]
    total: int
    page: int
    page_size: int
    total_pages: int


# ── PR #3: Top Players ──────────────────────────────────────────────


class TopPlayerEntry(BaseModel):
    player_id: UUID
    name: str
    category: str
    value: float | int  # the metric value


class TopLists(BaseModel):
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
    id: UUID
    name: str
    category: str
    avatar: str | None = None
    position: int | None = None
    points: int = 0
    matches: int = 0
    wins: int = 0
    losses: int = 0
    win_pct: float = 0.0
    sets_won: int = 0
    games_won: int = 0
    streak: int = 0


class ComparisonResult(BaseModel):
    player_a: ComparisonPlayer
    player_b: ComparisonPlayer
    same_category: bool = True
    category_name: str | None = None
    point_difference: int | None = None
    notice: str | None = None


# ── PR #3: H2H ─────────────────────────────────────────────────────


class H2HMatch(BaseModel):
    date: str | None = None
    winner_id: UUID | None = None
    winner_name: str | None = None
    sets_p1: int = 0
    sets_p2: int = 0
    games_p1: int = 0
    games_p2: int = 0
    resultado: str | None = None


class H2HResult(BaseModel):
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
    player_id: UUID
    name: str
    category: str
    value: float | int
    metric_key: str  # e.g. "points", "wins", "streak"
    metric_label: str  # e.g. "Puntos FEP", "Victorias"


class CategoryDetail(BaseModel):
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
    player_id: UUID
    name: str
    category: str
    current_points: int = 0
    sparkline: list[int] = []  # historical points — placeholder for now


class CommunityHighlights(BaseModel):
    most_points: PlayerBrief | None = None
    best_form: PlayerBrief | None = None
    best_pair: dict | None = None  # {player1_name, player2_name, win_pct, matches}
    most_active: PlayerBrief | None = None
