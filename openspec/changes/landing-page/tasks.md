# Tasks: Landing Page Redesign

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | 535–955 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | PR 1 (Foundation+Partials A) → PR 2 (Partials B) → PR 3 (JS) → PR 4 (Orchestrator+Verify) |
| Delivery strategy | force-chained |
| Chain strategy | feature-branch-chain |

Decision needed before apply: No
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units

| Unit | Goal | Likely PR | Base Branch | Notes |
|------|------|-----------|-------------|-------|
| 1 | Foundation + Partials A | PR 1 | `feature/landing-page` | base.html, views.py, landing.css, hero, features, cta |
| 2 | Partials B | PR 2 | PR 1 branch | metrics, rankings, ai_analysis, mockups, analytics |
| 3 | JavaScript modules | PR 3 | PR 2 branch | scroll, counters, scouter, charts, entry |
| 4 | Final orchestration + verify | PR 4 | PR 3 branch | index.html rewrite, cross-section verification |

## Phase 1: Foundation

- [x] 1.1 Add `{% block head_styles %}` to `base.html` before `</head>`
- [x] 1.2 Add `show_landing_nav` conditional CTA to navbar in `base.html`
- [x] 1.3 Add `landing_data` mock dict + `show_landing_nav=True` to `views.py` index()

## Phase 2: Partials A — No JS Dependencies

- [x] 2.1 Create `landing.css` with section layouts + 4 keyframes (lr-fade-in, lr-scan-line, lr-counter-tick, lr-glow-pulse)
- [x] 2.2 Create `_landing_hero.html` — scouter panel, power‑level counter, scan‑line, dual CTAs
- [x] 2.3 Create `_landing_features.html` — 6‑card grid via `{% for feature in landing_data.features %}`
- [x] 2.4 Create `_landing_cta.html` — gradient button reading `landing_data.cta`

## Phase 3: Partials B — Remaining Sections

- [x] 3.1 Create `_landing_metrics.html` — stats bar with `data-counter` attributes for animation targets
- [x] 3.2 Create `_landing_rankings.html` — rankings table + top‑3 player cards from `landing_data.rankings`
- [x] 3.3 Create `_landing_ai_analysis.html` — head‑to‑head comparison + improvement plan progress bars
- [x] 3.4 Create `_landing_mockups.html` — phone showcase `<img>` with `onerror` fallback placeholder
- [x] 3.5 Create `_landing_analytics.html` — radar `<canvas>`, stat bars, donut `<canvas>`

## Phase 4: JavaScript Modules

- [x] 4.1 Create `landing_scroll.js` — IntersectionObserver + rAF debounce, toggles `.is-visible` at 15% threshold
- [x] 4.2 Create `landing_counters.js` — rAF‑stepped numeral counter targeting `[data-counter]` elements
- [x] 4.3 Create `landing_scouter.js` — power‑level scan‑bar animation + glow‑pulse loop
- [x] 4.4 Create `landing_charts.js` — Chart.js radar + donut init, CDN‑fail placeholder fallback (spec scenario 12)
- [x] 4.5 Create `landing.js` — entry module: imports sub-modules, inits in order (scroll→counters→scouter→charts)

## Phase 5: Final Orchestration + Verification

- [x] 5.1 Rewrite `index.html` as orchestrator — extends `base.html`, 8 `{% include %}` in DOM order (spec 5)
- [x] 5.2 Verify all 10 sections render with correct DOM order (spec 5) — confirmed partial sequence: hero, metrics, features, analytics, rankings, ai_analysis, mockups, cta + navbar/footer base.html
- [ ] 5.3 Verify zero‑state: empty `landing_data` produces no 500 errors (spec 7) — needs runtime
- [ ] 5.4 Verify CSS isolation: navigate `/login`, `/dashboard` — no `.landing-*` interference (spec 9) — needs runtime
- [ ] 5.5 Verify JS module isolation: console has no cross‑contamination `ReferenceError` (spec 22) — needs runtime
