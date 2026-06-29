# Design: Tournament System

## Technical Approach

Extend the existing Clean Architecture layers — no repository abstraction added. Tournament CRUD uses the same **router → direct ORM** pattern as Players. Computed stats is a standalone query function, not a use case class, keeping infrastructure out of domain. Power level gets an optional `computed_stats` parameter — pure function stays pure. Frontend fetches computed stats via a dedicated endpoint on profile load.

---

## Architecture Decisions

| Option | Tradeoff | Decision |
|--------|----------|----------|
| **ComputedStats**: service class vs standalone function | Class adds ceremony (no state needed); function matches `calculate_power_level` pattern | Standalone function in `domain/use_cases/computed_stats.py` |
| **DI pattern**: formal container vs FastAPI Depends | Containers (like `dependency-injector`) require a new library + learning curve; existing code uses `Depends(get_db)` and manual use-case instantiation | Follow existing — `Depends(get_db)` in routers, manual construction |
| **Tournament CRUD**: use_case layer vs direct ORM | Adding use cases for simple CRUD is premature abstraction — no business logic beyond ownership guard | Direct ORM in `tournaments.py` (same as `players.py`) |
| **Data flow**: compute on every load vs cache | Stats change only when matches/tournaments change; single aggregation query is cheap (<5ms) | Compute on demand via `GET /players/{id}/stats`; no caching needed |
| **Power level**: pass computed_stats from handler vs inject DB in use case | Keeping use case infrastructure-free aligns with Clean Architecture; handler fetches and passes | Handler fetches `computed_stats`, passes to `AnalyzePlayerUseCase.execute(player, computed_stats=...)` |

---

## Data Flow (Key Sequences)

```
Create Tournament:
  Client → POST /tournaments/ → Pydantic validates (name max 200, strip_html)
  → TournamentModel(name, date, fep_points, owner_id=current_user.id)
  → db.commit() → return TournamentPublicSchema

Add Match with Tournament:
  Client → POST /players/{id}/matches { tournament_id, ronda, ... }
  → MatchModel(tournament_id=..., ...) → db.commit()
  → Tournament FK = NULL for amistosos

Load Player Profile:
  Client → GET /players/{id} (PlayerPublicSchema without competitive fields)
  → GET /players/{id}/stats (ComputedStats: torneos, win_rate, fep_points)
  → renderPlayer() + renderComputedStats() update DOM
```

---

## Data Model

```
UserModel (1) ────── (N) PlayerModel
UserModel (1) ────── (N) TournamentModel
PlayerModel (1) ──── (N) MatchModel (via player1_id OR player2_id)
TournamentModel (1) ── (N) MatchModel (tournament_id FK, nullable = amistoso)
```

### MatchModel Changes
| Column | Type | Nullable | Notes |
|--------|------|----------|-------|
| `tournament_id` | UUID FK→tournaments.id | YES | NULL = amistoso |
| `ronda` | String(100) | YES | Enums: Fase de grupos, 32avos, 16avos, Octavos, Cuartos, Semifinal, Final |
| `torneo` | String(150) | YES | **Kept** for migration safety, deprecated |

### PlayerModel Deletions
Drop columns: `torneos_jugados`, `victorias`, `puntos_ranking_fep`

---

## API Contracts

### New Endpoints (`/api/v1/tournaments/`)

| Method | Path | Auth | Ownership | Response | Status |
|--------|------|------|-----------|----------|--------|
| POST | `/tournaments/` | JWT | owner_id=current_user | TournamentPublicSchema | 201 |
| GET | `/tournaments/` | JWT | filter by owner_id | list[TournamentPublicSchema] | 200 |
| GET | `/tournaments/{id}` | JWT | check owner_id | TournamentPublicSchema | 200 |
| PUT | `/tournaments/{id}` | JWT | check owner_id | TournamentPublicSchema | 200 |
| DELETE | `/tournaments/{id}` | JWT | check owner_id | — | 204 |

**TournamentPublicSchema**: `id, name, date, fep_points, owner_id, created_at, match_count (computed)`

### Modified Match Schemas
- **MatchCreateSchema**: replace `torneo: str?` → `tournament_id: UUID?`, add `ronda: str?`
- **MatchPublicSchema**: same replacements
- **Matches GET** filter: `?tournament_id=<uuid>`, `?tournament_id=none` (amistosos)

### New Endpoint: `GET /players/{id}/stats`
Returns `{ torneos: int, win_rate: float, fep_points: int }`. Ownership-checked. Computed via raw SQL aggregation.

---

## Migration Plan

**New Alembic revision**: `parent = 5b1dcc84d45e`

| Step | Operation | Rollback |
|------|-----------|----------|
| 1 | `CREATE TABLE tournaments (...)` | `DROP TABLE tournaments` |
| 2 | `ALTER TABLE matches ADD tournament_id UUID`, `ADD ronda VARCHAR(100)` | `DROP COLUMN tournament_id, ronda` |
| 3 | Data backfill: unique `torneo` values → Tournament rows; `UPDATE matches SET tournament_id = t.id WHERE torneo = t.name` | `UPDATE matches SET torneo = (SELECT name FROM tournaments WHERE id = tournament_id)` + delete Tournament rows |
| 4 | `ALTER TABLE players DROP torneos_jugados, victorias, puntos_ranking_fep` | `ADD COLUMN` with defaults |

**Backfill safeguard**: `WHERE tournament_id IS NULL` to avoid double-setting on re-run. Group by `(torneo, player1_id)` to partition by user.

**Keep `torneo` column**: NOT dropped in this release. Deprecated but readable.

---

## Power Level Integration

```python
# power_level.py — before
def calculate_power_level(stats: PlayerStats, category: PlayerCategory) -> int
# after
def calculate_power_level(stats: PlayerStats, category: PlayerCategory,
                          computed_stats: ComputedStats | None = None) -> int
```

Competitive component replaced:
- **Old**: `stats.victorias / stats.torneos_jugados`, `stats.puntos_ranking_fep`
- **New** (when `computed_stats` provided): `computed_stats.win_rate / 100`, `computed_stats.fep_points`
- **Fallback** (None): `win_rate=0, fep_pts=0` — graceful degradation

**Caller update** (`analysis.py` → `AnalyzePlayerUseCase.execute`):
```python
computed_stats = get_computed_stats(db, player_id)
result = use_case.execute(player, computed_stats=computed_stats)
```

---

## OWASP Control Points

| ID | Risk | Control | Location |
|----|------|---------|----------|
| A01 | Broken Access Control | `current_user.id` filter on all tournament queries | `tournaments.py` every handler |
| A01 | Broken Access Control | Player ownership check on /stats endpoint | `players.py` get_player_stats |
| A03 | Injection | `strip_html()` on tournament `name` | `TournamentCreateSchema` validator |
| A03 | Injection | `Field(max_length=200)` on name | `TournamentCreateSchema` |
| A03 | Injection | SQLAlchemy ORM param queries | All queries use ORM or `text()` |
| A07 | Auth bypass | `Depends(get_current_user)` on all new endpoints | `tournaments.py`, player stats |
| XSS | Stored XSS | Tournament name in dropdowns via `textContent` / `escapeHtml()` | `player_detail.js` |

---

## Implementation Order

| Phase | Tasks | Depends on |
|-------|-------|------------|
| **1. DB + Domain** | TournamentModel, Tournament entity, MatchModel FK + ronda, Alembic + backfill | — |
| **2. Computed Stats** | get_computed_stats(), power_level update, AnalyzePlayerUseCase update, /stats endpoint | Phase 1 |
| **3. API** | tournaments.py CRUD, match schema changes, match endpoint updates, router registration | Phase 1 |
| **4. Frontend** | Tournament selector in match modal, match filter, stats card/bar/modal, form cleanup | Phase 2+3 |
| **5. Cleanup** | Drop player competitive columns, remove from schemas/entities/forms | Phase 4 verified |

---

## Open Questions

- [ ] Migration backfill: what if two users have a tournament with the same name? Current grouping by `(torneo, player1_id)` handles this — confirm approach with PO
- [ ] DELETE cascade: set tournament_id=NULL on related matches is correct, but should the `ronda` also be cleared? (spec says no — keep for audit)
