# Design: Landing Page Redesign

## Technical Approach

Replace the 56-line monolithic `index.html` with a DDR-extracted 10-section showcase. Each visual section is a dedicated partial (`_landing_*.html`) receiving data exclusively via Jinja context. `index.html` becomes a pure orchestrator — extends `base.html`, includes partials in DOM order. `views.py` passes a `landing_data` dict with mock values structured to mirror a future real API response. CSS isolation via `.landing-*` class prefix. JS scope isolation via ES modules (`type="module"`). No backend changes beyond the view layer.

## Architecture Decisions

| Decision | Choice | Alternatives | Rationale |
|---|---|---|---|
| Navbar rendering | Stay in `base.html` with `show_landing_nav` flag | Extract to `_landing_navbar.html` | Navbar structure is global (logo, brand, auth JS). Only the unauthenticated CTA link changes. A partial would mean duplicating the full navbar structure. |
| Data injection | `landing_data` context dict → partials read `landing_data.section.field` | Hardcoded values in partials, template globals | Swapping mock→real API data means changing dict keys in views.py, not touching 9 templates. Zero hardcoded display values in partials. |
| JS module system | ES `type="module"` with scoped imports | IIFE globals, no modules | Per-spec requirement 22: no variable cross-contamination. `type="module"` enforces scope isolation by design. Chart/API data passed via `<script id="landing-data" type="application/json">` — one DOM node parsed by each module independently. |
| Chart.js CDN failure | Degraded placeholder text per canvas | Silent fail, console error | Check `typeof Chart === 'undefined'` on init. Wraps each canvas in a `.landing-chart-wrapper`; on failure, replaces innerHTML with fallback text. Meets spec scenario 12. |
| Scroll debounce | `requestAnimationFrame` gate | Lodash throttle, raw observer | Native, zero-dependency. `ticking` flag ensures ≤1 DOM mutation per frame (~16ms). Meets spec scenario 14. |
| CSS scoping | `.landing-*` class prefix | Shadow DOM, BEM, scoped attribute | Existing scouter.css uses `.power-glow`, `.tab-active` — no overlap. Prefix approach is minimal and doesn't require a preprocessor. |

## Data Flow

```
views.py: index()
  │
  ├─ landing_data = {hero, metrics, features, analytics, rankings, ai_analysis, mockups, cta}
  └─ show_landing_nav = True
       │
       ▼
  index.html (extends base.html)
       │
       ├─ include "_landing_hero.html"        ←  landing_data.hero
       ├─ include "_landing_metrics.html"      ←  landing_data.metrics
       ├─ include "_landing_features.html"     ←  landing_data.features
       ├─ include "_landing_analytics.html"    ←  landing_data.analytics
       ├─ include "_landing_rankings.html"     ←  landing_data.rankings
       ├─ include "_landing_ai_analysis.html"  ←  landing_data.ai_analysis
       ├─ include "_landing_mockups.html"      ←  landing_data.mockups
       └─ include "_landing_cta.html"          ←  landing_data.cta
```

Each partial references only its slice: `{{ landing_data.hero.power_level }}`, `{% for f in landing_data.features %}`, etc. Missing or empty data degrades via Jinja `default()` / `if` guards — no 500 errors.

**landing_data shape**:

```python
landing_data = {
    "hero": {"power_level": 8400, "title": "...", "subtitle": "...", "cta_text": "Empezar análisis", "cta_url": "/login", "secondary_cta_text": "Ver API docs", "secondary_cta_url": "/docs"},
    "metrics": {"players_analyzed": 15234, "matches_processed": 89240, "tournaments_tracked": 456, "active_users": 3402},
    "features": [{"icon": "...", "title": "...", "description": "..."}],  # 6 items
    "analytics": {"radar_labels": [...], "radar_data": [...], "win_rate": 68, "stat_bars": [{"label": "...", "value": N}]},
    "rankings": {"top_players": [{"rank": 1, "name": "...", "power": 9850, "change": "+2"}], "player_rank": 42, "total_players": 15234},
    "ai_analysis": {"player1": {...}, "player2": {...}, "improvement_plan": [{"area": "...", "priority": "...", "progress": 35}]},
    "mockups": {"images": [{"src": "/static/img/...", "alt": "..."}]},
    "cta": {"title": "...", "subtitle": "...", "button_text": "Comenzar ahora", "button_url": "/register"},
}
```

## File Changes

| File | Action | Description |
|---|---|---|
| `app/templates/index.html` | Rewrite | 10-section orchestrator (navbar + 8 partials + footer in base.html): extends base.html, 8 `{% include %}` directives |
| `app/templates/base.html` | Modify | Add `{% block head_styles %}` before `</head>`; conditional `show_landing_nav` CTA |
| `app/api/v1/views.py` | Modify | index() passes `landing_data` + `show_landing_nav=True` |
| `app/templates/partials/_landing_hero.html` | Create | Scouter panel, power level counter, scan-line, CTAs |
| `app/templates/partials/_landing_metrics.html` | Create | Trusted-by stats bar with JS-counter targets |
| `app/templates/partials/_landing_features.html` | Create | 6-card grid via `{% for feature in landing_data.features %}` |
| `app/templates/partials/_landing_analytics.html` | Create | Radar canvas, stat bars, donut canvas |
| `app/templates/partials/_landing_rankings.html` | Create | Rankings table + top-3 player cards |
| `app/templates/partials/_landing_ai_analysis.html` | Create | Head-to-head comparison + improvement plan with progress bars |
| `app/templates/partials/_landing_mockups.html` | Create | Phone showcase with `onerror` fallback |
| `app/templates/partials/_landing_cta.html` | Create | Final CTA with gradient button |
| `app/static/css/landing.css` | Create | Section layouts, `.landing-*` classes, keyframes |
| `app/static/js/landing/landing.js` | Create | Entry: imports + inits sub-modules in order |
| `app/static/js/landing/landing_scroll.js` | Create | IntersectionObserver + rAF debounce |
| `app/static/js/landing/landing_counters.js` | Create | Numeral counter via rAF stepping |
| `app/static/js/landing/landing_scouter.js` | Create | Power level scan bar + glow |
| `app/static/js/landing/landing_charts.js` | Create | Chart.js radar/donut + CDN-fail fallback |

## Key Patterns

**`show_landing_nav` flag** (base.html, navbar CTA):
```jinja
<div class="flex items-center gap-4" id="nav-right">
  {% if show_landing_nav %}
    <a href="/register" class="..." style="color:#00FF87;">Empezar</a>
  {% else %}
    <a href="/login" class="..." style="color:#FF6B00;">Acceder</a>
  {% endif %}
</div>
```
The inline auth JS at base.html L75-102 overrides this for authenticated users — login state beats landing flag.

**Chart.js CDN failure** (landing_charts.js):
```js
export function init() {
  if (typeof Chart === 'undefined') {
    document.querySelectorAll('[data-chart]').forEach(el => {
      el.innerHTML = '<div class="landing-chart-fallback">Gráfico no disponible</div>';
    });
    return;
  }
  const data = JSON.parse(document.getElementById('landing-data').textContent);
  // ...init radar + donut from data.analytics
}
```

**Scroll debounce** (landing_scroll.js):
```js
let ticking = false;
new IntersectionObserver(entries => {
  if (!ticking) {
    requestAnimationFrame(() => {
      entries.forEach(e => e.target.classList.toggle('is-visible', e.isIntersecting));
      ticking = false;
    });
    ticking = true;
  }
}, { threshold: 0.15 });
```

**CSS keyframes** (landing.css):
- `@keyframes lr-fade-in`: opacity 0→1, translateY(30px)→0 — applied on `.landing-section.is-visible`
- `@keyframes lr-scan-line`: horizontal bar sweep across scouter panel
- `@keyframes lr-counter-tick`: brief scale(1.05) on digit change
- `@keyframes lr-glow-pulse`: text-shadow intensity cycle on power level

## Implementation Order

| Step | What | Independent? | Verification |
|---|---|---|---|
| 1 | `base.html`: `head_styles` block + `show_landing_nav` | Yes — no other changes needed | Any existing page loads without breakage |
| 2 | `views.py`: add `landing_data` mock dict | Yes | — |
| 3 | `landing.css`: base layouts + keyframes | Yes | Stylesheet loads on landing page |
| 4 | Partials A: `_landing_hero`, `_landing_features`, `_landing_cta` | No JS deps | Sections render with mock data |
| 5 | Partials B: `_landing_metrics`, `_landing_rankings`, `_landing_ai_analysis`, `_landing_mockups`, `_landing_analytics` | Independent from each other | Full page renders |
| 6 | JS: scroll → counters → scouter → charts → entry | Charts depend on Chart.js CDN | Animations trigger, no console errors |
| 7 | `index.html`: final orchestrator | Depends on all partials | All 10 sections in correct DOM order |

## Testing Strategy

| Layer | What to Test | Approach |
|---|---|---|
| Template rendering | All partials load without TemplateNotFound | Load `/`, inspect DOM for 10 sections |
| Context injection | `landing_data` keys match partial expectations | Pass empty dict, verify zero-state (0 counters, empty tables, no 500) |
| CSS isolation | No style leaks to non-landing pages | Navigate `/login`, `/dashboard` — no `.landing-*` style interference |
| JS: Chart.js failure | Degraded placeholder renders | Block chart.js CDN, reload — verify fallback text |
| JS: scroll animation | `is-visible` added once | Scroll page, verify class persists on re-scroll (spec 13) |
| JS: module isolation | No cross-contamination | Console — no `Uncaught ReferenceError` from module cross-reference (spec 22) |

## Migration / Rollout

No migration required. Rollback: revert `index.html`, `base.html`, `views.py`. Delete `landing.css` and `static/js/landing/`. All changes are additive frontend — zero data or API impact.
