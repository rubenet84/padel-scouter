# Tasks: Tournament System

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~900 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Phase 1+2) → PR 2 (Phase 3+4) → PR 3 (Phase 5) |
| Delivery strategy | ask-on-risk |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: pending
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Notes |
|------|------|-----------|-------|
| 1 | DB + Domain + Computed Stats | PR 1 (~300 lines) | Independent, can ship earlier |
| 2 | API + Frontend | PR 2 (~475 lines) | Depends on PR 1 DB schema existing |
| 3 | Cleanup (drop columns, remove fields) | PR 3 (~120 lines) | Depends on PR 2 being verified in prod |

---

## Phase 1: DB + Domain

- [ ] 1.1 Create `app/domain/entities/tournament.py` — `Tournament` dataclass with id, name, date, fep_points, owner_id, created_at
- [ ] 1.2 Add `TournamentModel` to `app/infrastructure/database/models.py` — table, columns, FK→users, relationship to MatchModel
- [ ] 1.3 Add `tournament_id` (UUID FK→tournaments.id, nullable) + `ronda` (String 100, nullable) columns to `MatchModel` + `tournament` relationship
- [ ] 1.4 Write Alembic migration `tournament_system_v1` (parent: `5b1dcc84d45e`): create `tournaments` table, add columns to `matches`, add FK
- [ ] 1.5 Data backfill: query distinct legacy `torneo` values, create Tournament rows, update FK on matching matches

## Phase 2: Computed Stats

- [ ] 2.1 Create `app/domain/use_cases/computed_stats.py` — `ComputedStats` dataclass + `get_computed_stats(db, player_id)` with raw SQL aggregation
- [ ] 2.2 Modify `calculate_power_level()` in `app/domain/value_objects/power_level.py` — accept optional `computed_stats: ComputedStats | None`, use computed win_rate/fep_points when provided
- [ ] 2.3 Update `AnalyzePlayerUseCase.execute()` in `app/domain/use_cases/analyze_player.py` — accept optional `computed_stats` param, pass to `calculate_power_level`
- [ ] 2.4 Update `app/api/v1/analysis.py` handler — fetch `computed_stats` via `get_computed_stats()`, pass to `use_case.execute(player, computed_stats=...)`
- [ ] 2.5 Add `GET /api/v1/players/{id}/stats` endpoint in `app/api/v1/players.py` — returns `ComputedStatsSchema` with ownership guard

## Phase 3: API

- [ ] 3.1 Create `app/schemas/tournament.py` — `TournamentCreateSchema` (strip_html validator, max_length=200), `TournamentUpdateSchema`, `TournamentPublicSchema`
- [ ] 3.2 Create `app/api/v1/tournaments.py` — CRUD router (POST, GET list w/ match_count, GET by id, PUT date/fep_points only, DELETE with SET NULL)
- [ ] 3.3 Update `app/schemas/player.py` — replace `torneo` with `tournament_id` + `ronda` in `MatchCreateSchema` and `MatchPublicSchema`
- [ ] 3.4 Update match POST/PUT in `app/api/v1/players.py` — accept `tournament_id`/`ronda`, add `tournament_id` query param filter on GET matches
- [ ] 3.5 Register tournament router in `app/main.py` — `app.include_router(tournaments_router, prefix="/api/v1")`

## Phase 4: Frontend

- [ ] 4.1 Update match create/edit modal in `player_detail.html` — replace amistoso/torneo toggle with tournament dropdown (load from API), inline create tournament, ronda selector
- [ ] 4.2 Add match history filter combo in `player_detail.html` — dropdown with "Todos"/"Amistosos"/"Torneo: X" options, filter via `?tournament_id=` param
- [ ] 4.3 Update stats card in `renderPlayer()` in `player_detail.html` — fetch `GET /players/{id}/stats`, populate torneos/win_rate/fep display
- [ ] 4.4 Update stats modal `openStatsModal()` — replace competitive section with async computed stats fetch
- [ ] 4.5 Update competitive bar in `renderPlayer()` — use computed stats async fetch instead of manual player data
- [ ] 4.6 Remove competitive fields from new player form in `dashboard.html` — delete "Historial Competitivo" section, update STATS constant, update `resetNewPlayerForm()` and `createPlayer()` validation
- [ ] 4.7 Remove competitive fields from edit player form in `player_detail.html` — delete "Historial Competitivo" section from edit modal, update `statFields` arrays, update validation in `saveAndAnalyze()`

## Phase 5: Cleanup

- [ ] 5.1 Drop `torneos_jugados`, `victorias`, `puntos_ranking_fep` from `PlayerModel` in `models.py` + write Alembic migration
- [ ] 5.2 Remove competitive fields from `PlayerStats` entity (`app/domain/entities/player.py`) and from `PlayerStatsSchema`/`PlayerPublicSchema` in `app/schemas/player.py`
- [ ] 5.3 Update unit tests in `tests/unit/test_power_level.py` + `tests/conftest.py` — update `PlayerStats` fixtures (remove competitive fields), add test for `computed_stats` param
- [ ] 5.4 Update integration tests in `tests/integration/test_database.py` — remove competitive fields from `PlayerModel` creation

## Dependencies

| Task | Depends On |
|------|-----------|
| 1.2 (TournamentModel) | 1.1 (Tournament entity) |
| 1.3 (MatchModel FK) | 1.2 (TournamentModel exists) |
| 1.4 (Alembic migration) | 1.2, 1.3 (models defined) |
| 1.5 (Backfill) | 1.4 (table exists) |
| Phase 2 (Computed Stats) | Phase 1 (DB schema) |
| Phase 3 (API) | Phase 1 (TournamentModel exists) |
| Phase 4 (Frontend) | Phase 2+3 (endpoints exist) |
| Phase 5 (Cleanup) | Phase 4 verified (safe to drop columns) |

## OWASP Checklist

| Concern | Applied In |
|---------|-----------|
| A01 Ownership guard | All tournament CRUD filters by `current_user.id`; stats endpoint checks player ownership |
| A03 Injection | Pydantic validation on all input schemas; `strip_html()` on tournament name; SQLAlchemy ORM/parameterized queries |
| A07 Authentication | `Depends(get_current_user)` on all new and modified endpoints |
| XSS | Tournament name rendered via `textContent`; `escapeHtml()` helper in templates |
| A05 Misconfiguration | TournamentPublicSchema exposes only metadata, no sensitive data |

## Estimated Changed Lines per File

| File | Change | Est. Lines |
|------|--------|-----------|
| `app/domain/entities/tournament.py` | NEW | 20 |
| `app/infrastructure/database/models.py` | Modify (add TournamentModel, extend MatchModel) | 35 |
| `alembic/versions/tournament_system_v1.py` | NEW | 80 |
| `app/domain/use_cases/computed_stats.py` | NEW | 50 |
| `app/domain/value_objects/power_level.py` | Modify (computed_stats param) | 15 |
| `app/domain/use_cases/analyze_player.py` | Modify (accept computed_stats) | 10 |
| `app/api/v1/analysis.py` | Modify (fetch & pass computed_stats) | 10 |
| `app/schemas/tournament.py` | NEW | 60 |
| `app/api/v1/tournaments.py` | NEW | 120 |
| `app/schemas/player.py` | Modify (match schemas, remove competitive) | 30 |
| `app/api/v1/players.py` | Modify (match endpoints + /stats endpoint) | 45 |
| `app/main.py` | Modify (register tournament router) | 3 |
| `app/templates/player_detail.html` | Modify (match modal, filter, stats, edit form) | 180 |
| `app/templates/dashboard.html` | Modify (remove competitive fields) | 40 |
| `app/domain/entities/player.py` | Modify (remove competitive fields + win_rate) | 10 |
| `tests/conftest.py` | Modify (update PlayerStats fixtures) | 15 |
| `tests/unit/test_power_level.py` | Modify (add computed_stats tests) | 25 |
| `tests/integration/test_database.py` | Modify (remove competitive fields) | 10 |
| **Total** | | **~900** |
