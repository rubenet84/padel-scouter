# Proposal: Tournament System

## Intent

Competitive stats (torneos_jugados, victorias, pts FEP) are manually entered — disconnected from matches. `torneo` is free-text, `ronda` is collected in UI but never persisted. This adds a Tournament entity, auto-computes stats from match data, and enables tournament-based filtering.

## Scope

**In**: TournamentModel CRUD, MatchModel tournament_id FK + ronda, drop 3 manual stat fields from PlayerModel, auto-computed competitive stats, match filter (Todos/Amistosos/Torneo:X), rename TORNEOS to PORCENTAJE DE VICTORIAS, OWASP on new endpoints, data migration.

**Out**: player2_id hack, result/resultado dedup, bracket management, multi-player tournament associations, power level formula changes.

## Capabilities

### New
- `tournament-management`: CRUD for tournaments with name, date, fep_points.
- `competitive-statistics`: auto-computed torneos, win%, FEP points from match data.

### Modified
None — first capability specs for this project.

## Approach

1. Add `TournamentModel` (id, name, date, fep_points, owner_id FK) in models.py
2. Add `tournament_id` FK + `ronda` string to `MatchModel`; drop `torneo` column
3. Tournament CRUD endpoints under `/api/v1/tournaments/`
4. Computed stats service: `torneos = COUNT(DISTINCT tournament_id)`, `victorias% = SUM(ganado)/COUNT(*)`, `pts FEP = SUM(t.fep_points)`
5. Remove competitive fields from `PlayerModel`, `PlayerStats`, all schemas and forms
6. `power_level.py` calls computed stats service via dependency injection
7. Migration: backfill `Tournament` rows from unique `torneo` values, set FK on matches
8. Frontend: tournament selector in match modal, filter combo on match history, relabel stats

## Affected Areas

| Area | Impact |
|------|--------|
| `app/domain/entities/player.py` | Modified — remove competitive fields |
| `app/domain/entities/tournament.py` | New entity |
| `app/infrastructure/database/models.py` | Modified — add TournamentModel, alter MatchModel |
| `app/schemas/player.py` | Modified — remove competitive fields |
| `app/schemas/tournament.py` | New |
| `app/api/v1/tournaments.py` | New CRUD |
| `app/api/v1/players.py` | Modified — drop competitive field handling |
| `app/domain/value_objects/power_level.py` | Modified — use computed stats service |
| `app/templates/player_detail.html` | Modified — forms, filter, labels |
| `app/templates/dashboard.html` | Modified — remove competitive fields from creation |

## Migration

1. Collect all unique non-null, non-empty `torneo` values → create Tournament rows with `fep_points=0`
2. `UPDATE matches SET tournament_id = t.id FROM tournaments t WHERE match.torneo = t.name`
3. `tournament_id = NULL` for matches with empty/null `torneo` (amistosos)
4. Keep `torneo` column nullable during transition; drop in follow-up release

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|------------|
| Power level breaks without manual stats | Medium | Computed service with fallback defaults |
| Migration loses existing torneo data | Low | Keep column, dry-run before production |
| UI regressions in match forms | Medium | Test all flows: create/edit/delete + filter |

## Rollback

1. DB: drop `tournament_id` + `ronda` columns, restore `torneo_jugados/victorias/puntos_ranking_fep`, restore `torneo` column values from backup
2. Code: `git revert`
3. `torneo` column preserved as nullable during migration — never dropped immediately

## Dependencies

- Alembic migration for new table + column alterations
- Computed stats service (service/repository layer)

## Success Criteria

- [ ] Stats display correctly without any manual input
- [ ] Adding a tournament match auto-updates the player's competitive stats
- [ ] Match history filter works: Todos / Amistosos / Torneo: X
- [ ] Power level output unchanged for same técnica/físico/mental values
- [ ] Existing matches with free-text `torneo` retain data through migration
- [ ] All forms reject the removed competitive fields
- [ ] OWASP: ownership checks on tournament CRUD, input validation, XSS-safe output
