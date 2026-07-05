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
- [x] 1.4 Run visual regression — compare layout, animations, glow effects, pinned extension blocker
- [x] 1.5 Run full common checklist

> **PR #1 progress**: ✅ Complete. All 5 tasks done. Visual validation confirmed.

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
- [x] 2.0 Generate dead code audit table — commit this FIRST as documentation, zero deletions yet
- [x] 2.1 Review and approve audit table (con el usuario si es necesario)
- [x] 2.2 Remove dead variables: `analysisData` (line 1280) and `pendingTournamentCallback` (line 3062)
- [x] 2.3 Remove dead `@keyframes starTwinkle` from `player_detail.css`
- [x] 2.4 Remove dead code found during audit
- [x] 2.5 Unify duplicate `escapeHtml`/`escHtml` — keep `escapeHtml` in `player_utils.js`
- [x] 2.6 Extract to `player_utils.js`: escapeHtml, removeAccentAndLowerCase, nivelAmenazaFromScore, dragonBallCount, getMatchTypeBadge, hasLesionNote, resolveCategoryKey, getTournamentNameById, showToast
- [x] 2.7 Wire `<script src="...player_utils.js">` import, replace `escHtml` with `escapeHtml` at all call sites
- [x] 2.8 Delete original function definitions from `player_detail.html`
- [x] 2.9 Run common checklist + Baseline UAT — page loads (200), all function calls intact, no `escHtml` remnants
- [x] 2.10 Update metrics table

> **Nota**: `strengthDescription`, `findMatchByKey`, `getKeyFromString`, `formatStreak`, `formatDate`, `formatResult` no existen como funciones nombradas en el código — son lógica inline. Diferidas a PRs posteriores por la REGLADEORO.

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

## PR #3 — State + Entry Point + DOM (infrastructure only)

**Objective**: Create `PlayerState` class, `player_dom.js` (infrastructure, not wired yet), and `player_detail.js` entry point. NO behavior changes.

**Definition of Done**: Three new files exist. Entry point is wired but calls the same functions. Globals migrated to state ONLY at the end. Zero visual/functional regressions.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_state.js` (~20 lines)
- CREATE: `app/static/js/player_detail/player_constants.js` (~30 lines)
- CREATE: `app/static/js/player_detail/player_dom.js` (~160 lines)
- CREATE: `app/static/js/player_detail/player_detail.js` (~50 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #2.

**Fase 1 — Crear infraestructura (sin usar todavía)**:
- [x] 3.1 Create `player_state.js` — minimal `PlayerState` class with properties only (player, matches, tournaments, players). **No getters/setters**. Export singleton `export const state = new PlayerState()`.
- [x] 3.2 Create `player_constants.js` — move `CATEGORY_LEVELS` from template to this file. Pure data, no dependencies.
- [x] 3.3 Create `player_dom.js` — `Object.freeze({...})` with ALL ~110 `document.getElementById()` references mapped. **Do NOT replace any calls yet** — infrastructure only.

**Fase 2 — Conectar entry point**:
- [x] 3.4 Create `player_detail.js` — `initPlayerDetail(playerId)` entry point with `type="module"`. Creates state, loads data, calls EXACTLY the same existing functions (`loadPlayer`, `loadTournaments`, etc.).
- [x] 3.5 Wire `player_detail.js` as the module entry point in `player_detail.html`. Keep old `<script>` block running alongside during migration.

**Fase 3 — Migrar estado (solo al final)**:
- [x] 3.6 Write global values to `state` after each data load (playerData → state.player, loadedMatches → state.matches, etc.). Keep old variables for compatibility.
- [x] 3.7 **ONLY AFTER validation**: delete `let playerData`, `let loadedMatches`, `let loadedTournaments` from template. Replace reads with `state.player`, `state.matches`, `state.tournaments`.
- [x] 3.8 Run common checklist + Baseline UAT

**NO incluido en este PR**:
- ❌ Reemplazar 110 `document.getElementById()` con `DOM.*` (diferido a PR #6+)
- ❌ Mover render, radar, CRUD, analytics, search, modales
- ❌ Getters/setters en PlayerState
- ❌ Cambiar ninguna función existente más allá de migrar globales

---

## PR #4 — Visuals (Radar + Power)

**Objective**: Extract `drawRadar()` into `player_radar.js` and all power-level rendering into `player_power.js`. Two independent modules — no shared state, functions, or canvas.

**Definition of Done**: Radar chart identical, dragon balls/golpe/shenron identical, `renderPlayer()` uses the extracted functions.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_radar.js` (~100 lines)
- CREATE: `app/static/js/player_detail/player_power.js` (~180 lines)
- MODIFY: `app/templates/player_detail.html`

**Dependencies**: PR #3.

**Extract → Integrate → Validate → Delete**:

- [x] 4.1 Create `player_radar.js` — extract `drawRadar(p)` (line 1079, ~102 lines). Classic script, no modules. Function signature stays identical.
- [x] 4.2 Create `player_power.js` — extract `animatePower(target)` (line 1181), `renderDragonBalls(nivel)` (line 1308), `renderShenron()` (line 1387), `renderGolpeDefinitivo(latest, player)` (line 1392). Classic script. All function signatures stay identical.
- [x] 4.3 Add script tags to `player_detail.html`:
  ```html
  <script src="/static/js/player_detail/player_radar.js"></script>
  <script src="/static/js/player_detail/player_power.js"></script>
  ```
  Loading order: player_radar.js → player_power.js → main inline script (player_radar before player_power since renderGolpeDefinitivo calls renderDragonBalls, but they're independent — player_radar doesn't call player_power and vice versa).
- [x] 4.4 Delete original function definitions from `player_detail.html`:
  - `drawRadar(p) { ... }` (lines 1079-1180)
  - `animatePower(target) { ... }` (lines 1181-1194)
  - `renderDragonBalls(nivel) { ... }` (lines 1308-1386)
  - `renderShenron() { ... }` (lines 1387-1391)
  - `renderGolpeDefinitivo(latest, player) { ... }` (lines 1392-1478)
- [x] 4.5 Visual validation: radar renders correctly, dragon ball count, golpe text, shenron animation
- [x] 4.6 Run common checklist + Baseline UAT

**Architecture**:
```
player_radar.js         player_power.js
    drawRadar(p)            animatePower(target)
                            renderDragonBalls(nivel)
                            renderShenron()
                            renderGolpeDefinitivo(latest, player)

renderPlayer() [stays in template] calls both (unchanged signatures)
```

**No incluido en este PR**:
- ❌ Mover `renderPlayer()` — diferido a PR #6
- ❌ Mover modales, CRUD, analytics, search
- ❌ Cambiar firmas de funciones
- ❌ Usar `player_dom.js` todavía

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
- [x] 5.1 Create `player_modals.js` — extract openStatsModal, closeStatsModal, closeMatchAnalyticsModal, openLevelGuideModal, closeLevelGuideModal, openEditModal, closeEditModal, sanitizeEditPlayerNumbers, openFullMatchHistory, openSearchedMatchHistory, closeMatchHistoryModal, closeMatchModal
- [x] 5.2 Create `player_search.js` — extract filterMatchesBySearch, filterMatchHistory, allServerMatches, searchedMatches state
- [x] 5.3 Wire script tags + remove originals from template
- [x] 5.4 Manual validation: open/close each modal type, search text matches, filter results (HTTP 200, all onclick references present, no console errors)
- [x] 5.5 Run common checklist — syntax OK, no duplicates, no dead functions remain

---

## PR #6A — Core Render (`player_render.js`)

**Objective**: Extract `renderPlayer()` and related functions into `player_render.js`. Wire `player_dom.js` BLOCK BY BLOCK — no mass replacement.

**Definition of Done**: Player header, stats, avatar, category, level, analysis render identically. `player_dom.js` wired for extracted blocks only.

**Affected files**:
- CREATE: `app/static/js/player_detail/player_render.js` (~250 lines)
- MODIFY: `app/templates/player_detail.html`
- MODIFY: `app/static/js/player_detail/player_detail.js` (entry point)

**Dependencies**: PR #3, PR #5.

**Principio**: migrar `player_dom.js` por bloques funcionales, no por reemplazo masivo. Cada bloque se extrae, integra con DOM.*, valida, y solo entonces se pasa al siguiente.

**Regla nueva**: una función extraída NO puede modificar más nodos del DOM que la función original. Si durante el refactor una función empieza a asumir responsabilidades que antes no tenía, se detecta y se revierte.

**Bloques funcionales** (en orden):

### Bloque 1 — Player Header
- [x] 6A.1 Wire `DOM.breadcrumbName`, `DOM.playerName`, `DOM.badgeCategory` in `player_dom.js` → already wired (PR #3)
- [x] 6A.2 Extract header rendering into `player_render.js` renderPlayer() using DOM.* instead of sub-function
- [x] 6A.3 Replace `document.getElementById('breadcrumb-name')` etc. with `DOM.breadcrumbName()` etc.
- [x] 6A.4 Delete original header lines from `renderPlayer()` in template
- [x] 6A.5 Validate: name and badge render identically

### Bloque 2 — Stats Bars
- [x] 6A.6 Wire bar stats in `player_dom.js` (already mapped: barTecnica, barTecnicaVal, etc.)
- [x] 6A.7 Extract bars rendering into `player_render.js` renderPlayer() using DOM.* instead of sub-function
- [x] 6A.8 Replace `document.getElementById('bar-tecnica')` etc. with `DOM.barTecnica()` etc.
- [x] 6A.9 Delete original bars lines, validate

### Bloque 3 — Stat Values
- [x] 6A.10 Wire `DOM.valRemate`, `DOM.valBandeja`, `DOM.valVoleaDerecha`, `DOM.valVoleaReves` (already wired)
- [x] 6A.11 Extract skill values into `player_render.js` renderPlayer() using DOM.* instead of sub-function
- [x] 6A.12 Replace getElementById calls, delete originals, validate

### Bloque 4 — Power / Analysis
- [x] 6A.13 Wire power/analysis DOM refs (already wired)
- [x] 6A.14 Extract power/analysis into `player_render.js` renderPlayer() using DOM.*
- [x] 6A.15 Replace, delete, validate

### Bloque 5 — Avatar
- [x] 6A.16 Wire avatar DOM refs (already wired)
- [x] 6A.17 Extract `setAvatar(url, onload)` and `uploadAvatar(event)` → `player_render.js`
- [x] 6A.18 Replace DOM.* refs in extracted functions, delete originals, validate

### Bloque 6 — Entry Point
- [x] 6A.19 Wire `window.DOM = DOM` in `player_detail.js` for classic script access
- [x] 6A.20 Delete original `renderPlayer()` definition from template (all blocks now in module)
- [ ] 6A.21 Run common checklist + Baseline UAT (pending on PR merge)

**No incluido en este PR**:
- ❌ Mover match rendering, tournament rendering (PR #6B)
- ❌ Mover CRUD, analytics, search (PR #7+)
- ❌ Reemplazar `document.getElementById` fuera de los bloques extraídos

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
| 1 | **PR #1** ✅ | → 3410 | 2343 | → **0** | 239 | 5 | 16 | 131 | 24 |
| 2 | PR #2 | | | 0 | | | | | |
| 3 | PR #3 | | | 0 | | | | | |
| 4 | **PR #4** ✅ | → **3055** | → **~1983** | 0 | 239 | 5 | 16 | 131 | 24 |
| 5 | PR #5 | | | 0 | | | | | |
| 6A | **PR #6A** ✅ | → **~2640** | → **~1797** | 0 | 213 (player_render.js) | 5 | 16 | 131 | 24 |
| 6B | PR #6B | | | 0 | | | | | |
| 7 | PR #7 | | | 0 | | | | | |
| 8A | PR #8A | | | 0 | | | | | |
| 8B | PR #8B | | | 0 | | | | | |
| — | **Objetivo** | **<700** | **0** | **0** | **<100** | **0** | **—** | **0** | **0** |

> El objetivo <700 líneas es referencia, no mandato. La métrica real es que cada archivo tenga responsabilidad única y cohesionada.
