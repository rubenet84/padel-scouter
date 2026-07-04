# Proposal: Global Stats & Ranking

## Intent

Users need a centralized view of all player performance across their account — rankings, comparisons, trends, and pair stats. Currently each player is isolated; cross-player aggregation, ranking, head-to-head, and partner analysis don't exist. This module provides a full global statistics dashboard scoped to a single user's data.

## Scope

**In**: Summary endpoint (total players/matches/sets/games/wins/losses), general + per-category ranking (FEP points = tournament_points × round_weight), side-by-side player comparison, top N lists (wins, %, streak, sets, games, finals, semis, tournaments won), per-category aggregated stats, pair/partner statistics, head-to-head match history, ranking evolution tracking, global filters (season, competition type, category) affecting ALL dashboard data, summary cards (leader, best %, totals) as initial dashboard view.

**Out**: Cross-user rankings, chart/graph libraries (CSS bars only), real-time updates, export/PDF.

## Capabilities

### New
- `global-stats-summary`: Aggregate totals — total players, matches, tournaments, friendlies, sets, games, ranking leader, best win %. Shown as visual cards at dashboard top.
- `player-ranking`: Ranking by FEP points (tournament_points × round_weight), sortable by wins/percentage/streak/matches. Filterable by season, competition type (all/tournaments/friendlies), category, date.
- `player-comparison`: Side-by-side comparison of two players with full stats. Category shown as-is, no coefficient adjustments.
- `top-players`: Independent top lists — most points, most wins, best %, most matches, most tournaments won, most finals, most semifinals, most sets won, most games won, longest streak.
- `category-stats`: Aggregate stats per player category.
- `partner-stats`: Pair statistics — best pair, most wins, highest %, most matches.
- `head-to-head`: Match history between two selected players.
- `ranking-evolution`: Player movement over time, points and win evolution.

### Modified
None — first global-stats capability specs.

## Approach

1. Create `app/api/v1/stats.py` — endpoints reusing existing `get_computed_stats()` and `get_match_analytics()` for FEP points and per-player stats, all scoped via `current_user.id`. All endpoints accept optional filters: `season`, `competition_type` (all/tournament/friendly), `category`, `date_from`, `date_to`.
2. Create `app/templates/global_stats.html` — single-page dashboard with summary cards at top, then tabbed sections for ranking, top players, categories, pairs, head-to-head, evolution.
3. Create `app/static/js/global_stats.js` — fetch logic, DOM rendering, sorting, comparison selection. Global filters affect ALL sections via re-fetch with filter params.
4. Modify `app/templates/base.html` — add nav link to the new stats page.
5. Ranking is simply the sum of FEP points per player (reusing existing `computed_stats.py` logic). Friendly matches contribute to stats only, not ranking points.

## Affected Areas

| Area | Impact | Description |
|------|--------|-------------|
| `app/api/v1/stats.py` | New | 9 read-only endpoints |
| `app/templates/global_stats.html` | New | Dashboard template with tabbed sections |
| `app/static/js/global_stats.js` | New | Frontend fetch + rendering |
| `app/templates/base.html` | Modified | Nav link to global stats |

## Risks

| Risk | Likelihood | Mitigation |
|------|------------|-------------|
| Aggregate query performance with 50+ players | Medium | Single-query summaries using raw SQL, reusing existing `computed_stats.py` patterns |
| Large dashboard page load | Low | Tabs load on-demand via JS sections |

## Rollback Plan

Revert nav link in `base.html`, delete `stats.py`, `global_stats.html`, `global_stats.js`.

## Dependencies

None beyond existing stack (FastAPI, SQLAlchemy 2.0, Jinja2, JWT auth).

## Success Criteria

- [ ] Summary cards show correct totals at dashboard top
- [ ] Global filters (season, competition type, category) affect ALL dashboard sections
- [ ] Ranking sorts by all 8 columns: points, wins, %, matches, sets won, games won, streak, name
- [ ] Per-category ranking filters by category correctly
- [ ] Player comparison shows side-by-side stats with category labels (no coefficient adjustments)
- [ ] Top players section shows all 10 independent rankings
- [ ] Head-to-head shows correct match history between two players
- [ ] Pair stats compute correctly based on shared `partner_id`
- [ ] All data scoped strictly to `current_user.id`
- [ ] Friendly matches count for stats but NOT for ranking points
- [ ] Every player name in any dashboard section is a clickable link to `/player/{id}`
