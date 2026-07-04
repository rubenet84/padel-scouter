# Tasks: Global Stats & Ranking

## Review Workload Forecast

~7 new files, ~1500–2000 lines total.

| Field | Value |
|-------|-------|
| Estimated changed lines | 1500–2000 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Dashboard) → PR 2 (Ranking + Filters) → PR 3 (Top + Compare + H2H) → PR 4 (Pairs + Categories + Evolution + Polish) |
| Delivery strategy | ask-on-risk |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No — user confirmed chain strategy and split
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units (Feature Branch Chain)

| Unit | Goal | Likely PR | Base Branch | Notes |
|------|------|-----------|-------------|-------|
| 1 | Summary dashboard vertical slice | PR 1 | `feature/global-stats` | Foundation + /summary cards working end-to-end |
| 2 | Rankings + Global Filters | PR 2 | `feature/global-stats` (rebased after PR 1) | Ranking table, category filter, sort, global filter bar |
| 3 | Top Players + Comparison + H2H | PR 3 | PR 2 branch | Depends on filters being wired |
| 4 | Pairs + Category Stats + Evolution + Polish | PR 4 | PR 3 branch | Remaining sections + final optimization |

## Phase 1: Foundation + Summary Dashboard (PR #1)

- [x] 1.1 Create `app/schemas/stats.py` — all Pydantic response schemas
- [x] 1.2 Create `global_stats.py` — `build_filters()`, `get_global_summary()`, `get_player_stats_batch()`
- [x] 1.3 Create `app/api/v1/stats.py` — `GET /summary` endpoint only
- [x] 1.4 Create `app/templates/global_stats.html` — summary cards section
- [x] 1.5 Create `app/static/js/global_stats.js` — summary fetch + cards render
- [x] 1.6 Modify `app/templates/base.html` — add `/global-stats` nav link
- [x] 1.7 Modify `app/main.py` — register stats router
- [x] 1.8 VERIFY: summary cards load at `/global-stats`

## Phase 2: Rankings + Global Filters (PR #2)

- [ ] 2.1 Add `get_rankings(db, user_id, sort_by, order, filters)` to `global_stats.py`
- [ ] 2.2 Add `GET /ranking` + `GET /ranking/{category}` to `stats.py`
- [ ] 2.3 Add filter bar (season, comp_type, category, date range) to HTML
- [ ] 2.4 Wire filter state to JS — all functions accept filter params
- [ ] 2.5 Add ranking table, sort handlers, category filter to JS
- [ ] 2.6 Add ranking section + category selector to HTML
- [ ] 2.7 VERIFY: ranking loads, sort toggles, global filters affect ranking

## Phase 3: Top Players + Comparison + H2H (PR #3)

- [ ] 3.1 Add `get_top_players(db, user_id, metric, limit, filters)` to `global_stats.py`
- [ ] 3.2 Add `GET /top` endpoint to `stats.py`
- [ ] 3.3 Add 10 top-list cards render to JS
- [ ] 3.4 Add top players grid section to HTML
- [ ] 3.5 Add `get_comparison()` + `get_h2h()` to `global_stats.py`
- [ ] 3.6 Add `GET /compare/{p1}/{p2}` + `GET /h2h/{p1}/{p2}` to `stats.py`
- [ ] 3.7 Add player selector + comparison/H2H render to JS
- [ ] 3.8 Add comparison + H2H sections to HTML
- [ ] 3.9 VERIFY: top lists, 2-player comparison, match history — all respect filters

## Phase 4: Pairs + Category Stats + Evolution + Polish (PR #4)

- [ ] 4.1 Add `get_pair_stats()`, `get_category_stats()`, `get_evolution()` to `global_stats.py`
- [ ] 4.2 Add `/categories`, `/pairs`, `/evolution` endpoints to `stats.py`
- [ ] 4.3 Add pairs/category/evolution render to JS
- [ ] 4.4 Add remaining sections to HTML
- [ ] 4.5 VERIFY: all dashboard sections functional with filters
- [ ] 4.6 Optimize: review N+1 queries, add indexes if needed
- [ ] 4.7 Final integration test: full dashboard loads without errors
