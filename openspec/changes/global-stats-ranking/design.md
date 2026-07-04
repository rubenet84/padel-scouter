# Design: Global Stats & Ranking

## Technical Approach

New `app/domain/value_objects/global_stats.py` houses all aggregation queries using raw SQL via `text()` + `db.execute()` — same pattern as existing `computed_stats.py`. Each endpoint in new `app/api/v1/stats.py` performs exactly **one aggregate query** per call (no N+1) scoped to `current_user.id`. Reuses `get_computed_stats()` from `computed_stats.py` for per-player FEP points when needed. Global filters (`season`, `competition_type`, `category`, `date_from`, `date_to`) applied as dynamic `WHERE` clauses.

All endpoints return `{success: true, data: ..., error: null}` via a Pydantic response model.

## Architecture Decisions

### Decision: Aggregation strategy — raw SQL vs ORM

| Option | Tradeoff |
|--------|----------|
| Raw SQL (`text()`) | Direct control, no ORM overhead, same pattern as `computed_stats.py` |
| SQLAlchemy ORM | More boilerplate for aggregations, harder to optimize multi-join queries |
| **Choice**: Raw SQL | Follows existing pattern. ORM is fine for single-row but overhead for GROUP BY / SUM / COUNT across all players. |

### Decision: Computed columns — streak, sets_won, games_won

| Option | Tradeoff |
|--------|----------|
| **SQL window functions** | Single round-trip, fast, but `resultado` parsing in SQL is fragile |
| Python post-processing | Simpler parsing (existing `analytics.py` proves it), easier to debug |
| **Choice**: Python | `resultado` (e.g. `"6-4 6-3"`) is stored as string — SQL parsing is error-prone. Load rows into Python, parse sets/games there via `int(parts[0]) > int(parts[1])` as `analytics.py` already does. Streak computed by ordering matches by date and scanning `ganado` in Python. |

### Decision: Frontend data loading — one endpoint vs lazy sections

| Option | Tradeoff |
|--------|----------|
| Single endpoint | Simple but slow — all 9 sections' data in one payload |
| **Separate endpoints, lazy** | Each tab fetches on first click. Initial load fast (~1 req for summary cards). Better UX. |
| **Choice**: Lazy | Load summary on page load. Ranking, top, categories, pairs, H2H, evolution each fetch when tab is first activated. Global filter change triggers re-fetch on current tab only. |

### Decision: Sorting — server-side vs client-side

| Option | Tradeoff |
|--------|----------|
| **Server-side** | Works for any dataset size. SQL `ORDER BY` is fast. Default option. |
| Client-side | Instant after first fetch but slow for 100+ rows. |
| **Choice**: Server-side default, client-side toggle for < 50 players | Ranking endpoint always sorts server-side via `sort_by` + `order` params. Frontend offers optional client-side re-sort (JS array sort) for convenience without extra request. |

### Decision: Response format — Pydantic `response_model` vs manual dict

| Option | Tradeoff |
|--------|----------|
| **Pydantic `response_model`** | Auto-validation, OpenAPI docs, consistent with existing `players.py` |
| Manual dict | Flexible but no schema enforcement |
| **Choice**: `response_model` | Project convention. New `app/schemas/stats.py` defines `ApiResponse[T]` generic wrapper and all per-endpoint schemas. |

## Data Flow

```
Browser ──→ global_stats.js ──fetch()──→ stats.py endpoints
                                              │
                                              ▼
                                       global_stats.py (6 funciones parametrizables)
                                               │
                                              ▼
                                      DB (SQL via text())
                                              │
                                    ┌─────────┴─────────┐
                                    ▼                   ▼
                          computed_stats.py        raw SQL results
                          (reused for FEP)         (GROUP BY, COUNT,
                                                     SUM, WINDOW)
                                              │
                                              ▼
                                      Python post-process
                                      (parse resultado → sets/games,
                                       compute streak, win_pct)
                                              │
                                              ▼
                                      Pydantic response → JSON
                                              │
                                              ▼
                                    global_stats.js render
                                    (tables, cards, tabbed sections)
```

## File Changes

| File | Action | Description |
|------|--------|-------------|
| `app/domain/value_objects/global_stats.py` | Create | ~6 funciones parametrizables. `get_global_summary(db, user_id, filters)`, `get_rankings(db, user_id, sort_by, order, filters)` — incluye ranking general y por categoría (misma función, filter param). `get_top_players(db, user_id, metric, limit)` — una sola función recibe el métrico (points/wins/pct/matches/sets/games/streak/tournaments_won/finals/semis) como parámetro. `get_comparison(db, user_id, p1, p2)`, `get_pair_stats(db, user_id, filters)`, `get_h2h(db, user_id, p1, p2)`, `get_evolution(db, user_id, filters)`. Cada función acepta `**filters` con season, competition_type, category, date_from, date_to. |
| `app/api/v1/stats.py` | Create | 9 endpoints, auth via `get_current_user`, DB via `get_db`. Each calls `global_stats.py` function, wraps in `ApiResponse`. |
| `app/schemas/stats.py` | Create | `ApiResponse`, `PlayerRankRow`, `GlobalSummary`, `PlayerBrief`, `ComparisonResult`, `TopLists`, `CategoryStats`, `PairStats`, `H2HResult`, `EvolutionData`. |
| `app/templates/global_stats.html` | Create | Dashboard with 6 tabbed sections + summary cards. Extends `base.html`. |
| `app/static/js/global_stats.js` | Create | Fetch functions per endpoint, render helpers, tab management, filter state, sort toggles. |
| `app/templates/base.html` | Modify | Add "Estadísticas" nav link in `#nav-right` after Dashboard when authenticated. |
| `app/main.py` | Modify | Add `from app.api.v1.stats import router as stats_router` and `app.include_router(stats_router, prefix="/api/v1")`. |

## Interfaces / Contracts

```python
# app/schemas/stats.py

class ApiResponse(BaseModel):
    success: bool
    data: dict | list | None
    error: str | None

class PlayerBrief(BaseModel):
    id: UUID
    name: str
    category: str
    points: int = 0
    win_pct: float = 0.0

class PlayerRankRow(PlayerBrief):
    position: int
    wins: int
    losses: int
    matches: int
    streak: int
    sets_won: int
    games_won: int

class GlobalSummary(BaseModel):
    total_players: int
    total_matches: int
    total_tournaments: int
    total_friendlies: int
    total_sets: int
    total_games: int
    ranking_leader: PlayerBrief | None
    best_win_pct: PlayerBrief | None
```

Query params inherited by all filterable endpoints:

```
GET /api/v1/stats/ranking?sort_by=points&order=desc&category=Profesional&season=2026&competition_type=all&date_from=&date_to=
```

## Routes

| Method | Path | Description |
|--------|------|-------------|
| GET | `/api/v1/stats/summary` | Aggregate totals + leader + best % |
| GET | `/api/v1/stats/ranking` | Full ranking with sort/filter |
| GET | `/api/v1/stats/ranking/{category}` | Per-category ranking |
| GET | `/api/v1/stats/compare/{p1}/{p2}` | Side-by-side player comparison |
| GET | `/api/v1/stats/top` | 10 top lists (5 entries each) |
| GET | `/api/v1/stats/categories` | Per-category aggregates (all 7 categories) |
| GET | `/api/v1/stats/pairs` | Pair/partner statistics |
| GET | `/api/v1/stats/h2h/{p1}/{p2}` | Head-to-head match history |
| GET | `/api/v1/stats/evolution` | Ranking movement over time |

## Frontend Architecture

- **Template**: `global_stats.html` — extends `base.html`, renders empty section divs. Summary cards at top. Tab navigation for Ranking, Top, Categories, Pairs, H2H, Evolution.
- **JS**: `global_stats.js` — state object `{ filters: {...}, activeTab: "...", data: {...} }`. On tab switch, if data not loaded → `fetch()` endpoint, then `render*()` function populates DOM. Filter changes reset tab's `data` and re-fetch.
- **Navigation**: All player names rendered as `<a href="/player/{id}">` for clickable profiles.
- **Sorting**: Click column header → `fetch()` with `sort_by=col&order=asc|desc`. Small datasets may re-sort client-side via toggle.

## Testing Strategy

| Layer | What to Test | Approach |
|-------|-------------|----------|
| Unit | Aggregation SQL queries | Mock DB with known rows, verify `global_stats.py` functions return correct aggregations |
| Unit | Python post-processing (streak, sets, games) | Test `parse_resultado()` and streak computation with edge cases (empty, single match, win/loss streaks) |
| Integration | All 9 endpoint responses | Test client with test DB, verify `ApiResponse` format and filter correctness |
| Integration | Filter params | Call each endpoint with/without filters, assert data scoping and expected row counts |
| Integration | Auth scoping | Verify 401 without token, 404 for other user's data |

No migration required — reads existing `players`, `matches`, `tournaments` tables.
