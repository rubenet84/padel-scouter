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
