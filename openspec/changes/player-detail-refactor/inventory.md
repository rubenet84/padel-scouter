# Inventario: `player_detail.html`

> **Archivo**: `C:\Users\Vpsc-FlashVolcano\Desktop\padel-scouter\app\templates\player_detail.html`
> **Total**: 3.619 líneas | **CSS**: 210 (5.8%) | **HTML**: 1.066 (29.4%) | **JS**: 2.343 (64.7%)
> **Fecha del análisis**: 2026-07-04

---

## 1. CSS — 210 líneas (líneas 5-214)

| Bloque | Líneas | Responsabilidad | Dependencias | Riesgo extracción | Prioridad |
|--------|--------|----------------|-------------|-------------------|-----------|
| `@keyframes` animaciones (14 animaciones) | 10-208 (~80) | Efectos visuales: scan, flicker, ki charge, glow, star twinkle, pulse ring | Ninguna (CSS puro) | 🟢 Bajo | 🟢 Baja |
| Layout / componentes | ~70 | Estilos de scrollbar, dragón balls, pulse-ring, stat bars | Ninguna | 🟢 Bajo | 🟢 Baja |
| Shenron wrapper / character glow | ~44 | Efectos glow para Goku, Gohan, Mr. Satan, Goku SSJ4 | Ninguna | 🟢 Bajo | 🟢 Baja |
| Pinterest extension blocker | 8 | Bloquea extensiones que rompen el layout | Ninguna | 🟢 Bajo | 🟢 Baja |

**Total CSS extraíble**: 210 líneas → `player_detail.css`
**Código duplicado detectado**: 4 animaciones glow con estructura idéntica (~36 líneas) — `gokuGlow`, `satanGlow`, `gohanGlow`, `goku4Glow`

---

## 2. HTML — 1.066 líneas (líneas 216-1271)

| Bloque | Líneas | Responsabilidad | Dependencias | Riesgo extracción | Prioridad |
|--------|--------|----------------|-------------|-------------------|-----------|
| **Background + breadcrumb** | 216-228 (13) | Fondo gradiente + grid + navegación | Jinja: `{% block content %}` | 🟢 Bajo | 🟢 Baja |
| **Loading / Error** | 232-243 (12) | Estado inicial y de error | JS: `loadPlayer()` lo ocuestra/muestra | 🟢 Bajo | 🟢 Baja |
| **Profile Card** | 253-318 (66) | Avatar, nombre, categoría, power level, quick stats | JS: `renderPlayer()`, `uploadAvatar()`, `setAvatar()` | 🟢 Bajo | 🟡 Media |
| **Golpe Definitivo Card** | 321-369 (49) | Special attack, dragon balls, videos, imágenes secciones ocultas | JS: `renderGolpeDefinitivo()`, `renderDragonBalls()`, `renderShenron()` | 🟢 Bajo | 🟡 Media |
| **AI Description Card** | 372-380 (9) | Descripción generada por IA | JS: `renderPlayer()` | 🟢 Bajo | 🟢 Baja |
| **Action Buttons** | 387-403 (17) | Editar, guía de niveles, dashboard | JS: `openEditModal()`, `openLevelGuideModal()` | 🟢 Bajo | 🟢 Baja |
| **Edit Modal** | 406-545 (140) | Formulario completo de edición de jugador (nombre, categoría, stats) | JS: `openEditModal()`, `closeEditModal()`, `saveAndAnalyze()`, `sanitizeEditPlayerNumbers()` | 🟡 Medio | 🟡 Media |
| **Radar Section** | 547-633 (87) | Radar chart + stat bars + sub-stats grid | JS: `drawRadar()`, `renderPlayer()`, `renderComputedStats()` | 🟡 Medio | 🟡 Media |
| **Match Section** | 635-661 (27) | Filtro + buscador + contenedor lista de partidos | JS: `loadMatches()`, `renderMatches()`, `filterMatchesBySearch()` | 🟡 Medio | 🟡 Media |
| **Add Match Modal** | 664-883 (220) | Formulario completo: tipo, partner, torneo (CRUD), ronda, rival, resultado, fecha, notas | JS: `saveMatch()`, `openMatchModal()`, `openEditMatchModal()`, `resetMatchForm()`, `toggleTorneo()`, `loadPartnerPlayers()`, `loadTournaments()`, `createTournamentInline()`, `saveTournamentEdit()`, `deleteSelectedTournament()`, `onTournamentSelect()`, `lockPartnerForTournament()` | 🟠 Medio-Alto | 🔴 Muy alta |
| **Match History Modal** | 884-920 (37) | Historial completo con ordenación | JS: `openFullMatchHistory()`, `renderFullMatchHistory()`, `setSortMode()`, `sortMatches()` | 🟡 Medio | 🟡 Media |
| **Strengths/Weaknesses** | 922-943 (22) | Fortalezas y debilidades del análisis IA | JS: `renderPlayer()` | 🟢 Bajo | 🟢 Baja |
| **Improvement Plan** | 946-954 (9) | Plan de mejora IA | JS: `renderPlayer()` | 🟢 Bajo | 🟢 Baja |
| **No Analysis CTA** | 957-966 (10) | Botón para analizar si no hay datos | JS: `renderPlayer()`, `analyzeNow()` | 🟢 Bajo | 🟢 Baja |
| **Stats Modal** | 974-1003 (30) | Estadísticas detalladas: técnica, físico, mental | JS: `openStatsModal()`, `closeStatsModal()` | 🟢 Bajo | 🟡 Media |
| **Match Analytics Modal** | 1006-1130 (125) | Análisis completo: partidos, sets, torneos, rondas, scoring | JS: `openMatchAnalyticsModal()`, `closeMatchAnalyticsModal()` | 🟠 Medio-Alto | 🔴 Muy alta |
| **Level Guide Modal** | 1132-1269 (138) | Guía de categorías estática (INICIACIÓN → PROFESIONAL) | JS: `openLevelGuideModal()`, `closeLevelGuideModal()` | 🟢 Bajo | 🟢 Baja |

---

## 3. JS — 2.343 líneas (líneas 1275-3617) — ~70 funciones

### 3.1 Estado Global — 10 líneas (1275-1284)

| Variable | Línea | Tipo | Viva/Muerta | Usada por |
|----------|-------|------|-------------|-----------|
| `token` | 1275 | const | ✅ VIVA | 15 funciones |
| `playerId` | 1278 | let | ✅ VIVA | 14 funciones |
| `playerData` | 1279 | let | ✅ VIVA | renderPlayer, openStatsModal, openEditModal, saveAndAnalyze |
| `analysisData` | 1280 | let | ❌ **MUERTA** | **NUNCA usada** |
| `loadedMatches` | 1281 | let | ✅ VIVA | 12 funciones |
| `loadedTournaments` | 1282 | let | ✅ VIVA | 8 funciones |
| `CATEGORY_LEVELS` | 1284 | const | ✅ VIVA | renderPlayer |

### 3.2 Constantes — 20 líneas

| Constante | Línea | Viva/Muerta | Usada por |
|-----------|-------|-------------|-----------|
| `SCOUTER_STAT_FIELDS` | 1505 | ✅ VIVA | `findStrongestStatFromPlayer()` |
| `ROUND_ORDER` | 2456 | ✅ VIVA | `getRoundIndex()`, `sortMatches()` |
| `sortMode` | 2299 | let | ✅ VIVA | `setSortMode()`, `sortMatches()` |
| `allServerMatches` | 2946 | let | ✅ VIVA | `filterMatchesBySearch()`, `onMatchFilterChange()` |
| `searchedMatches` | 2947 | let | ✅ VIVA | `filterMatchesBySearch()`, `openSearchedMatchHistory()` |
| `currentFilter` | 3354 | let | ✅ VIVA | `onMatchFilterChange()`, `loadMatches()` |
| `pendingTournamentCallback` | 3062 | let | ❌ **MUERTA** | **NUNCA usada** |

### 3.3 Mapa completo de funciones JS

| # | Función | Línea | LOCs | Complejidad | Riesgo | Dependencias (usa) | Dependencias (usada por) | Prioridad refactor |
|---|---------|-------|------|-------------|--------|-------------------|-------------------------|-------------------|
| 1 | `drawRadar(p)` | 1295 | 100 | 🟡 Media | 🟡 Medio | Ninguna | renderPlayer | 🟡 Media |
| 2 | `animatePower(target)` | 1397 | 12 | 🟢 Baja | 🟢 Bajo | Ninguna | renderPlayer | 🟢 Baja |
| 3 | `renderPlayer(p, analyses)` | 1411 | 93 | 🔴 Alta | 🟠 Alto | CATEGORY_LEVELS, SCOUTER_STAT_FIELDS, playerId, drawRadar, animatePower, renderGolpeDefinitivo, setAvatar, renderComputedStats → 30+ elementos DOM | loadPlayer, saveAndAnalyze | 🔴 Muy alta |
| 4 | `findStrongestStatFromPlayer(p)` | 1515 | 8 | 🟢 Baja | 🟢 Bajo | SCOUTER_STAT_FIELDS | renderGolpeDefinitivo | 🟢 Baja |
| 5 | `nivelAmenazaFromScore(score)` | 1524 | 6 | 🟢 Baja | 🟢 Bajo | Ninguna | renderGolpeDefinitivo | 🟢 Baja |
| 6 | `dragonBallCount(nivel)` | 1531 | 3 | 🟢 Baja | 🟢 Bajo | Ninguna | renderDragonBalls | 🟢 Baja |
| 7 | `renderDragonBalls(nivel)` | 1535 | 78 | 🟡 Media | 🟡 Medio | dragonBallCount → SVG HTML | renderGolpeDefinitivo | 🟡 Media |
| 8 | `renderShenron()` | 1614 | 4 | 🟢 Baja | 🟢 Bajo | Ninguna | renderGolpeDefinitivo | 🟢 Baja |
| 9 | `renderGolpeDefinitivo(latest, player)` | 1619 | 85 | 🟡 Media | 🟡 Medio | findStrongestStatFromPlayer, nivelAmenazaFromScore, renderDragonBalls, renderShenron → #golpe-card, #golpe-nombre, #dragon-balls-container, 4 secciones | renderPlayer | 🟡 Media |
| 10 | `uploadAvatar(event)` | 1706 | 48 | 🟡 Media | 🟡 Medio | token, playerId → POST /avatar, #avatar-spinner | inline onchange | 🟡 Media |
| 11 | `setAvatar(url, onload)` | 1755 | 28 | 🟢 Baja | 🟢 Bajo | #avatar-img, #avatar-placeholder | renderPlayer, uploadAvatar | 🟢 Baja |
| 12 | `escapeHtml(str)` | 1785 | 3 | 🟢 Baja | 🟢 Bajo | Ninguna | Múltiples render functions | 🟢 Muy alta |
| 13 | `showToast(msg, type)` | 1790 | 11 | 🟢 Baja | 🟢 Bajo | Ninguna | uploadAvatar, createTournamentInline, saveTournamentEdit, deleteMatch | 🟢 Baja |
| 14 | `loadPlayer()` | 1803 | 24 | 🟡 Media | 🟡 Medio | token, playerId → GET /players/{id}, GET /analysis/{id} | init, analyzeNow, saveAndAnalyze | 🟡 Media |
| 15 | `analyzeNow()` | 1828 | 22 | 🟡 Media | 🟡 Medio | token, playerId → POST /analysis/{id} | Botón onclick | 🟡 Media |
| 16 | `openStatsModal()` | 1851 | 39 | 🟡 Media | 🟡 Medio | playerData → #stats-tecnica/fisico/mental | Botón onclick | 🟡 Media |
| 17 | `closeStatsModal()` | 1891 | 3 | 🟢 Baja | 🟢 Bajo | #stats-modal | Escape, onclick close | 🟢 Baja |
| 18 | `openMatchAnalyticsModal()` | 1896 | **97** | 🔴 Alta | 🟠 Alto | token, playerId → GET /analytics → 15+ elementos DOM | Botón onclick | 🔴 Muy alta |
| 19 | `closeMatchAnalyticsModal()` | 1994 | 6 | 🟢 Baja | 🟢 Bajo | #match-analytics-modal | Escape, close btn | 🟢 Baja |
| 20 | `openLevelGuideModal()` | 2013 | 3 | 🟢 Baja | 🟢 Bajo | #level-guide-modal | Botón onclick | 🟢 Baja |
| 21 | `closeLevelGuideModal()` | 2016 | 3 | 🟢 Baja | 🟢 Bajo | #level-guide-modal | Escape, close btn | 🟢 Baja |
| 22 | `resolveCategoryKey(v)` | 2021 | 19 | 🟢 Baja | 🟢 Bajo | Ninguna | openEditModal | 🟢 Baja |
| 23 | `openEditModal()` | 2041 | 18 | 🟡 Media | 🟡 Medio | playerData → #edit-name, #edit-category, #e-* | Botón onclick | 🟡 Media |
| 24 | `closeEditModal()` | 2060 | 3 | 🟢 Baja | 🟢 Bajo | #edit-modal | Escape, save, close btn | 🟢 Baja |
| 25 | `sanitizeEditPlayerNumbers()` | 2064 | 7 | 🟢 Baja | 🟢 Bajo | input[number] en edit modal | init | 🟢 Baja |
| 26 | `saveAndAnalyze()` | 2072 | **88** | 🔴 Alta | 🟠 Alto | token, playerId → PUT /players/{id}, POST /analysis/{id} → valida 16 inputs | onclick save btn | 🔴 Muy alta |
| 27 | ~~`loadMatches()` (original)~~ | 2162 | 8 | — | — | **SOBREESCRITA** por línea 3381 (función #66) | loadPlayer (original) | 🟢 Baja |
| 28 | `getMatchTypeBadge(match)` | 2171 | 6 | 🟢 Baja | 🟢 Bajo | Ninguna | renderMatches, renderFullMatchHistory | 🟢 Baja |
| 29 | `hasLesionNote(notes)` | 2178 | 3 | 🟢 Baja | 🟢 Bajo | Ninguna | renderMatches, renderFullMatchHistory, saveMatch | 🟢 Baja |
| 30 | `renderMatches(matches, emptyMsg, searchCount)` | 2182 | **101** | 🔴 Alta | 🟠 Alto | loadedMatches, getMatchTypeBadge, escapeHtml, getTournamentNameById, playerId, **MATCH CARD TEMPLATE (66 LÍNEAS DUPLICADAS)** | loadMatches, filterMatchesBySearch | 🔴 Muy alta |
| 31 | `openFullMatchHistory()` | 2284 | 6 | 🟢 Baja | 🟢 Bajo | loadedMatches | Botón "Ver todo" | 🟢 Baja |
| 32 | `openSearchedMatchHistory()` | 2291 | 6 | 🟢 Baja | 🟢 Bajo | searchedMatches, loadedMatches | Enlace resultados | 🟢 Baja |
| 33 | `setSortMode(mode)` | 2301 | 24 | 🟡 Media | 🟢 Bajo | sortMode, searchedMatches, loadedMatches | Botones de ordenación | 🟢 Baja |
| 34 | `sortMatches(matches)` | 2326 | 27 | 🟡 Media | 🟡 Medio | sortMode, ROUND_ORDER | renderFullMatchHistory | 🟢 Baja |
| 35 | `renderFullMatchHistory(matches)` | 2354 | **74** | 🔴 Alta | 🟠 Alto | getMatchTypeBadge, hasLesionNote, escapeHtml, getTournamentNameById, sortMatches, playerId, **MATCH CARD TEMPLATE (65 LÍNEAS DUPLICADAS)** | openFullMatchHistory, openSearchedMatchHistory | 🔴 Muy alta |
| 36 | `closeMatchHistoryModal()` | 2429 | 5 | 🟢 Baja | 🟢 Bajo | #match-history-modal | openEditMatchModal, close btn | 🟢 Baja |
| 37 | `openMatchModal()` | 2435 | 9 | 🟡 Media | 🟡 Medio | token → loadPartnerPlayers | Botón "Nuevo partido" | 🟡 Media |
| 38 | `closeMatchModal()` | 2444 | 10 | 🟢 Baja | 🟢 Bajo | #match-modal, #btn-save-match | saveMatch, close btn, Escape | 🟢 Baja |
| 39 | `getRoundIndex(roundName)` | 2465 | 3 | 🟢 Baja | 🟢 Bajo | ROUND_ORDER | saveMatch | 🟢 Baja |
| 40 | `resetMatchForm()` | 2469 | **49** | 🟡 Media | 🟡 Medio | unlockPartnerSection, toggleTorneo → 15+ elementos DOM | openMatchModal, closeMatchModal | 🟡 Media |
| 41 | `toggleTorneo()` | 2519 | 15 | 🟡 Media | 🟡 Medio | #m-tipo, #torneo-fields, #amistoso-rival-field | resetMatchForm, onchange, openEditMatchModal | 🟡 Media |
| 42 | `validateResultString(result)` | 2536 | 34 | 🟡 Media | 🟡 Medio | Ninguna | saveMatch | 🟡 Media |
| 43 | **`saveMatch()`** | 2571 | **239** | 🔴🔴 **CRÍTICA** | 🔴 **Alto** | token, playerId, loadedMatches, loadedTournaments, hasLesionNote, validateResultString, getRoundIndex, ROUND_ORDER → 15+ elementos DOM → POST/PUT /matches | onclick #btn-save-match | 🔴🔴 Muy alta |
| 44 | `renderComputedStats(pid)` | 2812 | 28 | 🟡 Media | 🟡 Medio | token → GET /stats → #stat-torneos, #stat-winrate, #stat-fep, #bar-comp | renderPlayer, saveMatch, saveTournamentEdit, deleteMatch | 🟡 Media |
| 45 | `loadPartnerPlayers()` | 2842 | 26 | 🟡 Media | 🟡 Medio | token, playerId → GET /players/ | openMatchModal, openEditMatchModal | 🟡 Media |
| 46 | `onPartnerSelect()` | 2869 | 9 | 🟢 Baja | 🟢 Bajo | #m-partner-select, #m-partner-name | onchange | 🟢 Baja |
| 47 | `lockPartnerForTournament(name)` | 2879 | 22 | 🟡 Media | 🟡 Medio | escHtml → partner DOM | onTournamentSelect, openEditMatchModal | 🟡 Media |
| 48 | `unlockPartnerSection()` | 2902 | 10 | 🟢 Baja | 🟢 Bajo | partner DOM | resetMatchForm, onTournamentSelect | 🟢 Baja |
| 49 | **`escHtml(str)` — DUPLICADO** | 2913 | 6 | 🟢 Baja | 🟢 Bajo | **DUPLICADO de escapeHtml (línea 1785)** | lockPartnerForTournament | 🔴 Muy alta (unificar) |
| 50 | `loadTournaments()` | 2921 | 23 | 🟡 Media | 🟡 Medio | token, playerId → GET /tournaments | init, saveTournamentEdit | 🟡 Media |
| 51 | `getTournamentNameById(id)` | 2949 | 5 | 🟢 Baja | 🟢 Bajo | loadedTournaments | renderMatches, renderFullMatchHistory, saveMatch, openEditMatchModal | 🟢 Baja |
| 52 | `filterMatchesBySearch()` | 2955 | **84** | 🔴 Alta | 🟠 Alto | allServerMatches, loadedTournaments, hasLesionNote, getTournamentNameById, renderMatches → 26 formatos de fecha | oninput, onMatchFilterChange, loadMatches | 🟠 Alta |
| 53 | `filterMatchHistory()` | 3040 | 15 | 🟡 Media | 🟢 Bajo | loadedTournaments, onMatchFilterChange | createTournamentInline, saveTournamentEdit, etc. | 🟢 Baja |
| 54 | `loadTournamentFilterOptions()` | 3056 | 4 | 🟢 Baja | 🟢 Bajo | Ninguna | init | 🟢 Baja |
| 55 | `showNewTournamentForm()` | 3064 | 15 | 🟢 Baja | 🟢 Bajo | 6 elementos DOM | onclick | 🟢 Baja |
| 56 | `cancelNewTournament()` | 3080 | 3 | 🟢 Baja | 🟢 Bajo | #new-tournament-form | createTournamentInline, close btn | 🟢 Baja |
| 57 | `createTournamentInline()` | 3084 | **85** | 🔴 Alta | 🟠 Alto | token, playerId, loadedTournaments → POST /tournaments → 4 elementos DOM → actualiza select | onclick create btn | 🔴 Muy alta |
| 58 | `getSelectedTournament()` | 3171 | 6 | 🟢 Baja | 🟢 Bajo | loadedTournaments, #m-torneo-select | onTournamentSelect, show/edit/delete | 🟢 Baja |
| 59 | `onTournamentSelect()` | 3178 | 44 | 🟡 Media | 🟡 Medio | loadedMatches, getSelectedTournament, lockPartnerForTournament, unlockPartnerSection, onPartnerSelect | onchange, createTournamentInline, saveTournamentEdit, openEditMatchModal | 🟡 Media |
| 60 | `showTournamentEditForm()` | 3223 | 14 | 🟢 Baja | 🟢 Bajo | getSelectedTournament | onclick edit btn | 🟢 Baja |
| 61 | `cancelTournamentEdit()` | 3238 | 4 | 🟢 Baja | 🟢 Bajo | #edit-tournament-form | saveTournamentEdit, cancel btn | 🟢 Baja |
| 62 | `saveTournamentEdit()` | 3243 | **71** | 🔴 Alta | 🟠 Alto | token, loadedTournaments, getSelectedTournament → PUT /tournaments/{id} | onclick save btn | 🔴 Muy alta |
| 63 | `deleteSelectedTournament()` | 3315 | 37 | 🟡 Media | 🟡 Medio | token, loadedTournaments, getSelectedTournament → DELETE /tournaments/{id} | onclick delete btn | 🟡 Media |
| 64 | `onMatchFilterChange()` | 3356 | 23 | 🟡 Media | 🟡 Medio | token, playerId → GET /matches | onchange, filterMatchHistory | 🟡 Media |
| 65 | **`loadMatches()` — override** | 3381 | 20 | 🟡 Media | 🟠 Alto | **SOBREESCRIBE la original (línea 2162)**, token, playerId, currentFilter → GET /matches | Todo lo que llama a loadMatches | 🔴 Muy alta |
| 66 | `bindSaveMatchButton` (IIFE) | 3409 | 8 | 🟢 Baja | 🟢 Bajo | saveMatch, #btn-save-match | init | 🟢 Baja |
| 67 | Input validation init | 3419 | 17 | 🟢 Baja | 🟢 Bajo | input[number] | init | 🟢 Baja |
| 68 | **`openEditMatchModal(matchId)`** | 3439 | **125** | 🔴🔴 **CRÍTICA** | 🔴 **Alto** | token, playerId, loadedTournaments, getTournamentNameById, toggleTorneo, loadPartnerPlayers, onPartnerSelect, lockPartnerForTournament → GET /matches/{id} → 15+ elementos DOM | onclick edit match btn | 🔴🔴 Muy alta |
| 69 | `deleteMatch(matchId)` | 3565 | 42 | 🟡 Media | 🟡 Medio | token, playerId → DELETE /matches/{id} | onclick delete btn | 🟡 Media |
| 70 | Mute toggle listener | 3609 | 9 | 🟢 Baja | 🟢 Bajo | #unmute-btn, #goku-video | document click | 🟢 Baja |

---

## 4. Código Duplicado

| # | Descripción | Líneas | Total duplicado | Impacto |
|---|-------------|--------|-----------------|---------|
| 1 | **Match Card Template Literal** — `renderMatches` (línea 2231) y `renderFullMatchHistory` (línea 2396) tienen IDÉNTICA estructura HTML para cada match | 66 + 65 = **131** | 🔴🔴 **Crítico** — cualquier cambio visual requiere modificar ambos sitios |
| 2 | **`escapeHtml` vs `escHtml`** — dos implementaciones distintas del mismo sanitizador (líneas 1785 y 2913) | 3 + 6 = 9 | 🟠 Alto — diferente comportamiento (regex vs DOM) |
| 3 | **Animaciones glow CSS** — `gokuGlow`, `satanGlow`, `gohanGlow`, `goku4Glow` con idéntica estructura | ~9 c/u = ~36 | 🟡 Medio — 4 bloques casi idénticos |
| 4 | **Patrón de error** — `errEl.textContent = msg; errEl.classList.remove('hidden');` repetido ~15 veces en saveMatch, saveAndAnalyze, createTournamentInline, saveTournamentEdit | ~3 c/u | 🟢 Bajo — patrón, no duplicación exacta |

---

## 5. Código Muerto

| Variable/Función | Línea | Motivo |
|------------------|-------|--------|
| `analysisData` | 1280 | Declarada como `let`, NUNCA asignada ni leída |
| `pendingTournamentCallback` | 3062 | Declarada como `let`, NUNCA usada |
| ~~`loadMatches()` original~~ | 2162 | Sobreescrita en línea 3381 por la versión con filtros |

---

## 6. Funciones Excesivamente Grandes (>50 líneas)

| # | Función | Líneas | Prioridad de refactor |
|---|---------|--------|----------------------|
| 1 | `saveMatch()` | **239** | 🔴🔴 **Máxima** |
| 2 | `openEditMatchModal(matchId)` | **125** | 🔴🔴 **Máxima** |
| 3 | `renderMatches()` | **101** | 🔴 **Muy alta** (incluye 66 líneas duplicadas) |
| 4 | `drawRadar(p)` | **100** | 🟡 Media |
| 5 | `openMatchAnalyticsModal()` | **97** | 🔴 **Muy alta** |
| 6 | `renderPlayer()` | **93** | 🔴 **Muy alta** |
| 7 | `saveAndAnalyze()` | **88** | 🔴 **Muy alta** |
| 8 | `renderGolpeDefinitivo()` | **85** | 🟡 Media |
| 9 | `createTournamentInline()` | **85** | 🔴 **Muy alta** |
| 10 | `filterMatchesBySearch()` | **84** | 🟠 Alta |
| 11 | `renderDragonBalls()` | **78** | 🟡 Media |
| 12 | `renderFullMatchHistory()` | **74** | 🔴 **Muy alta** (incluye 65 líneas duplicadas) |
| 13 | `saveTournamentEdit()` | **71** | 🔴 **Muy alta** |
| 14 | `renderMatches` template literal | 66 | 🔴 **Muy alta** (duplicado) |
| 15 | `renderFullMatchHistory` template literal | 65 | 🔴 **Muy alta** (duplicado) |
| 16 | `resetMatchForm()` | 49 | 🟡 Media (borde, casi 50) |

---

## 7. Dependencias Críticas entre Bloques

```
renderPlayer() (orquestador principal)
├── drawRadar()           → canvas (independiente)
├── animatePower()        → DOM (independiente)
├── renderGolpeDefinitivo() → dragon balls + video (independiente)
├── setAvatar()           → DOM (independiente)
├── renderComputedStats() → API + DOM (independiente)
└── 30+ actualizaciones DOM directas

saveMatch() (operación crítica)
├── validateResultString()
├── getRoundIndex()
├── hasLesionNote()
├── getTournamentNameById()
├── loadMatches() → renderMatches()
└── renderComputedStats()

loadMatches() → renderMatches()
  └── getMatchTypeBadge()
  └── getTournamentNameById()
  └── escapeHtml()

match-card template (DUPLICADO en 2 sitios)
  └── getMatchTypeBadge()
  └── hasLesionNote()
  └── getTournamentNameById()
  └── escapeHtml()
  └── playerId (links a /player/{id})
```

---

## 8. Resumen de Prioridades de Refactor

| Prioridad | Bloques | Líneas | Motivo |
|-----------|---------|--------|--------|
| 🔴🔴 **Crítica** | saveMatch(), openEditMatchModal() | 364 | Mayor riesgo y tamaño |
| 🔴 **Muy alta** | Match Card duplicado, renderMatches, renderFullMatchHistory, saveAndAnalyze, createTournamentInline, saveTournamentEdit, openMatchAnalyticsModal | ~600 | Duplicación + tamaño + impacto visual |
| 🟠 **Alta** | filterMatchesBySearch(), renderPlayer() | 177 | Tamaño + acoplamiento |
| 🟡 **Media** | drawRadar, renderGolpeDefinitivo, renderDragonBalls, openStatsModal, loadPartnerPlayers, resetMatchForm, toggleTorneo | ~450 | Independientes, riesgo medio |
| 🟢 **Baja** | CSS, escapeHtml unificar, dead code, constantes, utilidades, modales simples | ~350 | Sin dependencias de lógica de negocio |
