# Tasks: Player Detail Refactor

## Review Workload Forecast

| Field | Value |
|-------|-------|
| Estimated changed lines | ~2,050 |
| 400-line budget risk | High |
| Chained PRs recommended | Yes |
| Suggested split | 10 stacked PRs (PR #1 → #10) |
| Delivery strategy | ask-always |
| Chain strategy | feature-branch-chain |

Decision needed before apply: Yes
Chained PRs recommended: Yes
Chain strategy: feature-branch-chain
400-line budget risk: High

### Suggested Work Units (10 PRs)

| PR | Goal | Est. lines | Depends on | Risk |
|----|------|:----------:|------------|:----:|
| **#1** | CSS extraction | ~210 | None — standalone | 🟢 |
| **#2** | Dead code + Utils | ~120 | PR #1 | 🟢 |
| **#3** | State + Entry Point + DOM | ~150 | PR #2 | 🟢 |
| **#4** | Visuals (Radar + Power) | ~220 | PR #3 | 🟡 |
| **#5** | Modals + Search | ~100 | PR #3 | 🟢 |
| **#6A** | Core Render (`player_render.js`) | ~250 | PR #3, PR #5 | 🟡 |
| **#6B** | Match + Tournament Rendering | ~200 | PR #6A | 🟡 |
| **#7** | Infrastructure (API + Partials) | ~300 | PR #6B | 🟡 |
| **#8A** | Feature — `player_matches.js` | ~350 | PR #7 | 🔴 |
| **#8B** | Feature — `player_analytics.js` | ~150 | PR #7 | 🟡 |

---

## Common Checklist for All PRs

**Technical**
- [ ] No functional changes (pure refactor)
- [ ] No visual changes (design, colors, sizes, text identical)
- [ ] No known regressions
- [ ] No new duplication
- [ ] No new global variables
- [ ] No browser console warnings
- [ ] No server errors (uvicorn)

**Code quality**
- [ ] No function >100 lines (or documented justification)
- [ ] No file >700 lines
- [ ] Dependencies documented
- [ ] Imports ordered
- [ ] No dead code (original or new)

**Manual**
- [ ] Create match
- [ ] Edit match
- [ ] Delete match
- [ ] Open match analytics
- [ ] Radar correct (stats, labels)
- [ ] Power level correct (dragon balls, golpe)
- [ ] Search/filters correct
- [ ] Modals open and close correctly

**Arquitectura**
- [ ] No aumenta el acoplamiento entre módulos
- [ ] No aparecen nuevas variables globales
- [ ] Se reduce la complejidad respecto al estado anterior
- [ ] La responsabilidad del nuevo módulo está claramente definida

**Visual regression**
- [ ] Compare page visually before/after — no changes in layout, spacing, colors, animations, or behavior

---

## Definition of Success (cada PR)

Más allá del checklist, un PR está realmente completo cuando:

- [ ] El usuario no percibe ningún cambio funcional
- [ ] El código es más pequeño o más simple que antes
- [ ] La responsabilidad del módulo extraído es más clara
- [ ] El siguiente PR resulta más sencillo que antes (no más difícil)
- [ ] Se reduce deuda técnica medible (métrica >0 en la tabla)

---

## Baseline UAT (repetir en cada PR)

Misma UAT exacta los 10 PRs. No pensar qué probar, solo ejecutar.

- [ ] Abrir ficha de jugador (`/player/{id}`)
- [ ] Cambiar entre pestañas (Partidos / Historial)
- [ ] Editar jugador (abrir modal, cambiar datos, guardar)
- [ ] Crear partido (todos los campos, guardar)
- [ ] Editar partido (abrir, modificar, guardar)
- [ ] Eliminar partido (confirmar eliminación)
- [ ] Ver historial completo de partidos
- [ ] Abrir Analytics de un partido
- [ ] Ver Radar de estadísticas
- [ ] Ver Power Level
- [ ] Ver Dragon Balls
- [ ] Ver Golpe Definitivo
- [ ] Buscar partidos por texto (filtro)
- [ ] Abrir y cerrar todos los modales (editar, stats, analytics, level guide, match)
- [ ] Responsive móvil (viewport <768px)
- [ ] Responsive escritorio (viewport ≥768px)

---

## PR #1 — CSS Extraction

**Objective**: Extract all 210 lines of inline `<style>` from `player_detail.html` into `player_detail.css`.

**Definition of Done**: CSS file exists, HTML links it, original `<style>` block removed, visual regression passes.

**Affected files**:
- CREATE: `app/static/css/player_detail.css` (~210 lines)
- MODIFY: `app/templates/player_detail.html` (remove `<style>`, add `<link>`)

**Dependencies**: None (standalone).

**Extract → Integrate → Validate → Delete**:
- [x] 1.1 Extract all 210 lines of CSS (lines 5-214) into `player_detail.css`, consolidate 4 duplicate glow animations into one shared `@keyframes charGlow`
- [x] 1.2 Add `<link rel="stylesheet" href="{{ url_for('static', filename='css/player_detail.css') }}">` in HTML `<head>`
- [x] 1.3 Remove original `<style>...</style>` block
- [ ] 1.4 Run visual regression — compare layout, animations, glow effects, pinned extension blocker
- [ ] 1.5 Run full common checklist

> **PR #1 progress**: Tasks 1.1–1.3 complete (extraction + integration + deletion). Tasks 1.4–1.5 require manual server + browser validation.

**Metrics after PR #1**:
| Metric | Before | After | Delta |
|--------|:------:|:-----:|:-----:|
| Lines `player_detail.html` | 3619 | 3410 | **−209** |
| JS inline (lines) | 2343 | 2343 | 0 |
| CSS inline (lines) | 210 | 0 | **−210** |
| Functions >50 lines | 16 | 16 | 0 |
| Duplicated code (lines) | 131 | 131 | 0 |
| Global variables | 24 | 24 | 0 |
| `document.getElementById()` | ~60 | ~60 | 0 |

---

## PR #2 — Dead Code + Utils

**Objective**: Remove dead variables and create `player_utils.js` with all pure utility functions.

**Definition of Done**: Dead code audit completed and reviewed. Dead variables removed. `escHtml`/`escapeHtml` unified. All pure utility functions living in `player_utils.js`. No render/fetch/CRUD/analytics/radar/power code touched.

**Definition of Success**: player_detail.html más pequeño y sin código muerto. Cualquier función de utilidad se encuentra en un solo lugar. El PR #3 arranca con una base más limpia.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_utils.js` (~80 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #1.

### Dead code audit (PRIMER COMMIT — cero eliminaciones todavía)

El primer entregable del PR #2 es la auditoría. Sin borrar nada. Solo documentar.

```markdown
## Dead Code Audit

### Variables sin uso
- `analysisData` (línea 1280) — 0 referencias
- `pendingTournamentCallback` (línea 3062) — 0 referencias

### Funciones duplicadas
- `escapeHtml` (línea ~1785) vs `escHtml` (línea ~2913)
- _(añadir más durante auditoría)_

### Listeners huérfanos
- _(buscar addEventListener sin removeEventListener correspondiente)_

### Constantes/referencias sin uso
- `@keyframes starTwinkle` (CSS) — 0 animation: references
- _(añadir más durante auditoría)_
```

Revisar la tabla. **Solo cuando esté aprobada**, continuar con las tareas de eliminación.

**Extract → Integrate → Validate → Delete**:
- [ ] 2.0 Generate dead code audit table — commit this FIRST as documentation, zero deletions yet
- [ ] 2.1 Review and approve audit table (con el usuario si es necesario)
- [ ] 2.2 Remove dead variables: `analysisData` (line 1280) and `pendingTournamentCallback` (line 3062)
- [ ] 2.3 Remove dead `@keyframes starTwinkle` from `player_detail.css` (identified in PR #1 — never referenced by any animation property)
- [ ] 2.4 Remove dead code found during audit (listeners huérfanos, constantes sin referencia)
- [ ] 2.5 Unify duplicate `escapeHtml` (line 1785) and `escHtml` (line 2913) — keep one implementation in `player_utils.js`
- [ ] 2.6 Extract to `player_utils.js`: escapeHtml, removeAccentAndLowerCase, strengthDescription, findMatchByKey, getKeyFromString, formatStreak, formatDate, formatResult, showToast, getMatchTypeBadge, hasLesionNote, dragonBallCount, nivelAmenazaFromScore, resolveCategoryKey
- [ ] 2.7 Wire `<script src="...player_utils.js">` import, replace all call sites
- [ ] 2.8 Delete original function definitions from `player_detail.html`
- [ ] 2.9 Run common checklist + Baseline UAT
- [ ] 2.10 Update metrics table

### Alcance explícito para PR #2

**SÍ incluye**:
- ✅ Eliminar variables/funciones/listeners/constantes nunca usados
- ✅ Unificar utilidades duplicadas en `player_utils.js`
- ✅ Mover utilidades puras a `player_utils.js`

**NO incluye** (se toca en PRs posteriores):
- ❌ Nada de render
- ❌ Nada de fetch/API
- ❌ Nada de CRUD
- ❌ Nada de analytics
- ❌ Nada de radar
- ❌ Nada de dragon balls / power level / golpe definitivo

---

## PR #3 — State + Entry Point + DOM

**Objective**: Create `PlayerState` class, centralized `DOM` object, and `player_detail.js` entry point.

**Definition of Done**: Zero global variables for state. All `document.getElementById()` in `player_dom.js`. Entry point calls `init*()`.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_state.js` (~40 lines)
- CREATE: `app/static/js/player_detail/player_dom.js` (~60 lines)
- CREATE: `app/static/js/player_detail/player_detail.js` (~40 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #2.

**Extract → Integrate → Validate → Delete**:
- [ ] 3.1 Create `player_state.js` — `PlayerState` class with properties (player, matches, tournaments, players), getters/setters
- [ ] 3.2 Create `player_dom.js` — `Object.freeze({...})` with all 30+ `document.getElementById()` references (see design.md §4)
- [ ] 3.3 Create `player_detail.js` — `initPlayerDetail(playerId)` that loads data via API calls and calls `initRadar()`, `initMatches()`, `initAnalytics()`, `initSearch()`
- [ ] 3.4 Replace global variables in `player_detail.html` (playerId, playerData, loadedMatches, loadedTournaments, CATEGORY_LEVELS) with `PlayerState` instance
- [ ] 3.5 Wire ES module imports — use `type="module"` on the entry point script tag
- [ ] 3.6 Delete original `let`/`const` declarations
- [ ] 3.7 Run common checklist

---

## PR #4 — Visuals (Radar + Power)

**Objective**: Extract `drawRadar()` and all power-level rendering into `player_radar.js` and `player_power.js`.

**Definition of Done**: Radar chart identical, dragon balls/golpe/shenron identical, `renderPlayer()` starts using these modules.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_radar.js` (~100 lines)
- CREATE: `app/static/js/player_detail/player_power.js` (~120 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #3.

**Extract → Integrate → Validate → Delete**:
- [ ] 4.1 Create `player_radar.js` — extract `drawRadar()` (line 1295, 100 lines), split into `drawRadarGrid()`, `drawRadarData()`, `drawRadar()`
- [ ] 4.2 Create `player_power.js` — extract `animatePower()` (line 1397), `renderDragonBalls()` (line 1535, 78 lines), `renderGolpeDefinitivo()` (line 1619, 85 lines), `renderShenron()` (line 1614)
- [ ] 4.3 Wire imports in `player_detail.js` entry point — `initRadar()`, power init is called from `playerRender` or directly
- [ ] 4.4 Delete original function definitions from `player_detail.html`
- [ ] 4.5 Visual validation: radar labels/data, dragon ball count, golpe text, shenron animation
- [ ] 4.6 Run common checklist

---

## PR #5 — Modals + Search

**Objective**: Extract all modal open/close logic into `player_modals.js` and search/filter into `player_search.js`.

**Definition of Done**: All modals open/close identically. Search and filter matches work as before.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_modals.js` (~50 lines)
- CREATE: `app/static/js/player_detail/player_search.js` (~50 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #3.

**Extract → Integrate → Validate → Delete**:
- [ ] 5.1 Create `player_modals.js` — extract openEditModal (line 2041), closeEditModal (line 2060), openStatsModal (line 1851), closeStatsModal (line 1891), openLevelGuideModal (line 2013), closeLevelGuideModal (line 2016), closeMatchAnalyticsModal (line 1994), closeMatchHistoryModal (line 2429), closeMatchModal (line 2444), overlay/dimmer utils
- [ ] 5.2 Create `player_search.js` — extract filterMatchesBySearch (line 2955, 84 lines), filterMatchHistory (line 3040), allServerMatches, searchedMatches state
- [ ] 5.3 Wire imports, remove originals
- [ ] 5.4 Manual validation: open/close each modal type, search text matches, filter results
- [ ] 5.5 Run common checklist

---

## PR #6A — Core Render (`player_render.js`)

**Objective**: Extract the main rendering orchestrator into `player_render.js`.

**Definition of Done**: Player header, stats, computed stats, avatar, tabs render identically.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_render.js` (~250 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #3, PR #5.

**Extract → Integrate → Validate → Delete**:
- [ ] 6A.1 Create `player_render.js` — extract `renderPlayer()` (line 1411, 93 lines), `renderComputedStats()` (line 2812, 85 lines), `setAvatar()` (line 1755), `uploadAvatar()` (line 1706), `findStrongestStatFromPlayer()` (line 1515), `renderMatchesHeader()`, `renderTabs()` — call into radar, power, match rendering modules
- [ ] 6A.2 Wire `playerRender(dom, state)` into `player_detail.js` entry point
- [ ] 6A.3 Delete original function definitions from `player_detail.html`
- [ ] 6A.4 Visual validation: player name, photo, category, level, computed stats, avatar upload
- [ ] 6A.5 Run common checklist

---

## PR #6B — Match + Tournament Rendering

**Objective**: Extract match and tournament rendering into `match_renderer.js` and `tournament_renderer.js`, unify duplicate match card template.

**Definition of Done**: 131 lines of duplicate match card template consolidated into one `renderMatchCard()`. Match lists and tournament display identical.

**Affected files**:
- CREATE: `app/static/js/player_detail/match_renderer.js` (~120 lines)
- CREATE: `app/static/js/player_detail/tournament_renderer.js` (~80 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #6A.

**Extract → Integrate → Validate → Delete**:
- [ ] 6B.1 Create `match_renderer.js` — extract `renderMatches()` (line 2182, 101 lines, includes 66-line duplicate template), `renderFullMatchHistory()` (line 2354, 74 lines, includes 65-line duplicate template). Create unified `renderMatchCard()` from the 131-line duplicate
- [ ] 6B.2 Create `tournament_renderer.js` — extract `renderTournaments()`, tournament modal rendering
- [ ] 6B.3 Wire into entry point, remove originals from `player_detail.html`
- [ ] 6B.4 Visual validation: match cards identical in list and history, tournament list correct
- [ ] 6B.5 Run common checklist

---

## PR #7 — Infrastructure (API + Partials)

**Objective**: Create `player_api.js` with all `fetch()` calls and split HTML into 6 Jinja partials.

**Definition of Done**: All API calls centralized. `player_detail.html` uses `{% include %}` for all partials. Zero inline fetch calls remain in HTML.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_api.js` (~150 lines)
- CREATE: `app/templates/partials/player_header.html`
- CREATE: `app/templates/partials/player_matches.html`
- CREATE: `app/templates/partials/player_radar.html`
- CREATE: `app/templates/partials/player_power.html`
- CREATE: `app/templates/partials/player_analytics.html`
- CREATE: `app/templates/partials/player_modals.html`
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #6B.

**Extract → Integrate → Validate → Delete**:
- [ ] 7.1 Create `player_api.js` — extract `loadPlayer()` (line 1803), `loadMatches()` (line 3381), `loadTournaments()` (line 2921), `deleteMatchFromDB()` (line 3565), `saveAndAnalyze()` API subset (line 2072), `analyzeNow()` (line 1828), `loadPartnerPlayers()` (line 2842), `sanitizeEditPlayerNumbers()` (line 2064), `getRoundIndex()` (line 2465) — all use `token` from state
- [ ] 7.2 Split HTML sections from `player_detail.html` into 6 partials under `templates/partials/`
- [ ] 7.3 Rebuild `player_detail.html` layout using `{% include 'partials/player_*.html' %}` for each section
- [ ] 7.4 Wire `player_api.js` import — entry point passes API functions to `init*()` calls
- [ ] 7.5 Delete original inline fetch calls and HTML sections from `player_detail.html`
- [ ] 7.6 Run common checklist — focus on API calls working (create match, load data, delete)

---

## PR #8A — Feature: `player_matches.js`

**Objective**: Extract the complete match CRUD lifecycle into `player_matches.js` — the largest and riskiest module.

**Definition of Done**: Create, edit, delete match works. Tournament CRUD works. Form validation works. All original functions removed.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_matches.js` (~350 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #7.

**Extract → Integrate → Validate → Delete**:
- [ ] 8A.1 Create `player_matches.js` — extract `saveMatch()` (line 2571, 239 lines), `openEditMatchModal()` (line 3439, 125 lines), `editMatch()`, `deleteMatch()` (line 3565, 42 lines), `validateResultString()` (line 2536, 34 lines), `saveAndAnalyze()` logic portion (line 2072, 88 lines), `openMatchModal()` (line 2435), `resetMatchForm()` (line 2469), `toggleTorneo()` (line 2519), `createTournamentInline()` (line 3084, 85 lines), `saveTournamentEdit()` (line 3243, 71 lines), `deleteSelectedTournament()` (line 3315, 37 lines), `onMatchFilterChange()` (line 3356), `onPartnerSelect()` (line 2869), `lockPartnerForTournament()` (line 2879), `unlockPartnerSection()` (line 2902), `openMatchModal()`, `showNewTournamentForm()` (line 3064), `cancelNewTournament()` (line 3080), `getSelectedTournament()` (line 3171), `onTournamentSelect()` (line 3178, 44 lines), `showTournamentEditForm()` (line 3223), `cancelTournamentEdit()` (line 3238), `bindSaveMatchButton()`
- [ ] 8A.2 Wire `initMatches(dom, state, api)` into entry point — passes DOM refs, state, API functions
- [ ] 8A.3 Delete all original match/tournament functions from `player_detail.html`
- [ ] 8A.4 Full manual validation: create match with all fields, edit match, delete match, tournament CRUD, form validation errors, search/filter after create, analytics after save
- [ ] 8A.5 Run common checklist

---

## PR #8B — Feature: `player_analytics.js`

**Objective**: Extract match analytics and history sorting into `player_analytics.js`.

**Definition of Done**: Analytics modal, match history modal, sorting all work identically.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_analytics.js` (~150 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #7.

**Extract → Integrate → Validate → Delete**:
- [ ] 8B.1 Create `player_analytics.js` — extract `openMatchAnalyticsModal()` (line 1896, 97 lines), `closeMatchAnalyticsModal()` (line 1994), `setSortMode()` (line 2301), `sortMatches()` (line 2326), `openFullMatchHistory()` (line 2284), `openSearchedMatchHistory()` (line 2291), `analyzeNow()` analytics portion
- [ ] 8B.2 Wire `initAnalytics(dom, state, api)` into entry point
- [ ] 8B.3 Delete original analytics/history/sort functions from `player_detail.html`
- [ ] 8B.4 Manual validation: open analytics modal for a match, verify data displayed, sort matches, open full history
- [ ] 8B.5 Run common checklist
- [ ] 8B.6 Final validation: confirm `player_detail.html` has zero JS inline (only `{% block scripts %}`)

---

## Metrics Tracking

Cada PR actualiza esta tabla. El valor **Before** de cada PR es el **After** del PR anterior.

| # | PR | player_detail.html | JS inline | CSS inline | Función más larga | Func. >100 | Func. >50 | Código dup. | Globales |
|:-:|----|:------------------:|:---------:|:----------:|:-----------------:|:----------:|:---------:|:-----------:|:--------:|
| — | Inicial | 3619 | 2343 | 210 | 239 | 5 | 16 | 131 | 24 |
| 1 | **PR #1** | → 3410 | 2343 | → **0** | 239 | 5 | 16 | 131 | 24 |
| 2 | PR #2 | | | 0 | | | | | |
| 3 | PR #3 | | | 0 | | | | | |
| 4 | PR #4 | | | 0 | | | | | |
| 5 | PR #5 | | | 0 | | | | | |
| 6A | PR #6A | | | 0 | | | | | |
| 6B | PR #6B | | | 0 | | | | | |
| 7 | PR #7 | | | 0 | | | | | |
| 8A | PR #8A | | | 0 | | | | | |
| 8B | PR #8B | | | 0 | | | | | |
| — | **Objetivo** | **<700** | **0** | **0** | **<100** | **0** | **—** | **0** | **0** |

> El objetivo <700 líneas es referencia, no mandato. La métrica real es que cada archivo tenga responsabilidad única y cohesionada.
