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

- [x] 2.1 Add `get_rankings(db, user_id, sort_by, order, filters)` to `global_stats.py`
- [x] 2.2 Add `GET /ranking` + `GET /ranking/{category}` to `stats.py`
- [x] 2.3 Add filter bar (season, comp_type, category, date range) to HTML
- [x] 2.4 Wire filter state to JS — all functions accept filter params
- [x] 2.5 Add ranking table, sort handlers, category filter to JS
- [x] 2.6 Add ranking section + category selector to HTML
- [x] 2.7 VERIFY: ranking loads, sort toggles, global filters affect ranking

## Phase 3: Top Players + Comparison + H2H (PR #3) — Análisis Competitivo

- [x] 3.1 Add `get_top_players(db, user_id, metric, limit, filters)` to `global_stats.py`
- [x] 3.2 Add `GET /top` endpoint to `stats.py`
- [x] 3.3 Add 10 top-list cards render to JS
- [x] 3.4 Add top players grid section to HTML
- [x] 3.5 Add `get_comparison()` + `get_h2h()` to `global_stats.py`
- [x] 3.6 Add `GET /compare/{p1}/{p2}` + `GET /h2h/{p1}/{p2}` to `stats.py`
- [x] 3.7 Add player selector + comparison/H2H render to JS
- [x] 3.8 Add comparison + H2H sections to HTML
- [x] 3.9 VERIFY: top lists, 2-player comparison, match history — all respect filters

## Phase 4: Polish + Records + Category Stats + Evolution + Community Card (PR #4 — FINAL)

This is the finishing PR. The focus is on making the module feel like a polished product.

### 4A — `GET /stats/records`
New endpoint that returns community records — reuses the same FEP/computation logic from Top. No new schemas needed (uses TopPlayerEntry or similar).

Records shown:
- Most streak (🔥)
- Most wins (✅)
- Most points (🏆)
- Most tournaments won (🏅)
- Most finals (🏁)
- Most semi-finals (🔶)
- Most sets won (📊)
- Most games won (🎾)

### 4B — `GET /stats/categories/{slug}?player_limit=5`
Enhanced category stats per category. Shows all categories + per category:
- Total players, total matches, wins, losses, avg win%, avg points, medals, leader (player name + points)
- If `player_limit > 0`, also include top N players sorted by points

Add schema `CategoryDetail` with all those fields.

### 4C — `GET /stats/evolution`
Evolution endpoint. Returns current points per player with a placeholder for historical sparkline data.
Schema: `EvolutionEntry { player_id, name, category, current_points, sparkline: [] }`
Sparkline stays empty for now — component ready for future historical data.

### 4D — `GET /stats/community`
Community highlights card. Returns:
- Player with most points
- Best form (highest win %, min 1 match)
- Best pair (pair with highest win %, min 2 matches together)
- Most active (most matches played)

Add schema `CommunityHighlights`.

### 4E — Polish
- CSS transitions/animations on filter changes, sort changes, page navigation
- Skeleton loading screens for all sections (summary, ranking, top, compare, h2h, records, categories, evolution, community)
- Homogeneous empty states: same pattern everywhere (icon + message + suggestion)
- Mobile responsive: ensure all tables scroll horizontally, grid cols collapse, filter bar wraps
- Query optimization: review for N+1 patterns, add missing indexes if needed

### Tasks

- [x] 4.1 Update `schemas/stats.py`: add `CategoryDetail`, `EvolutionEntry`, `CommunityHighlights`
- [x] 4.2 Add backend functions to `global_stats.py`:
  - `get_records()` — community records (reuses top logic)
  - `get_category_details()` — enhanced per-category stats
  - `get_evolution()` — per-player points with sparkline placeholder
  - `get_community_highlights()` — best pair, most active, etc.
- [x] 4.3 Add endpoints to `stats.py`: `GET /records`, `GET /categories`, `GET /categories/{category}`, `GET /evolution`, `GET /community`
- [x] 4.4 Update `global_stats.js`:
  - Load + render community records section
  - Load + render enhanced category stats
  - Load + render evolution (sparkline-ready)
  - Load + render community highlights card in summary
  - Skeleton loaders for EVERY section
  - CSS animations for filter/sort/page changes
  - Ensure `syncUrl()` handles all new params
  - Responsive: test all grid layouts collapse on small screens
- [x] 4.5 Update `global_stats.html`:
  - Add records grid section
  - Add categories detail section (per category cards)
  - Add evolution section (sparkline-ready)
  - Add community highlights card in summary area
  - All new sections hidden by default, revealed by JS
  - Skeleton placeholders in every section
- [x] 4.6 Remove old placeholders (`future-sections`, `pairs-section`)
- [x] 4.7 Add DB indexes if missing (player_id, owner_id, tournament_id, played_at)
- [x] 4.8 VERIFY: all 11 endpoints functional — server starts and all routes register correctly
- [x] 4.9 Final integration test: full app loads without Python errors, all routes serve responses
