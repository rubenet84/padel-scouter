# Audit: saveMatch() — Player Match CRUD

> **PR #8A — Commit 1**: Auditoría previa a la extracción de `player_matches.js`.
> Fecha: 2026-07-06

## 1. Call Graph

```
saveMatch()                                          [template inline, line 638]
 │
 ├── toggleTorneo()                                  [template inline, line 586]
 │   └── DOM: m-tipo, torneo-fields, amistoso-rival-field, new-tournament-form
 │
 ├── validateResultString(result)                    [template inline, line 603]
 │   └── Pura (0 side effects). Valida formato FIP 2026.
 │
 ├── hasLesionNote(notas) ⚠️ BUG                     [REFERENCIA PERDIDA]
 │   └── Se eliminó del template en PR #2 (#280328d) con nota "moved to player_utils.js"
 │   └── NUNCA se agregó a player_utils.js
 │   └── IMPACTO: saveMatch() lanza ReferenceError si se ejecuta
 │
 ├── getRoundIndex(ronda)                            [match_renderer.js]
 │
 ├── closeMatchModal()                               [player_modals.js]
 │
 ├── loadMatches()                                   [template inline, line 512]
 │   └── → fetchMatches(playerId, filter)            [player_api.js]
 │   └── → filterMatchesBySearch()                   [player_search.js]
 │
 ├── renderComputedStats(playerId)                   [template inline, line 851]
 │   └── → fetchPlayerStats(pid)                     [player_api.js]
 │   └── DOM writes: stat-torneos, stat-winrate, stat-fep, bar-comp, bar-comp-val
 │
 └── apiSaveMatch / updateMatch                      [player_api.js]
     └── → POST /api/v1/players/{id}/matches
     └── → PUT /api/v1/players/{id}/matches/{id}

openEditMatchModal(matchId)                          [template inline, line 1258]
 │
 ├── closeMatchHistoryModal()                        [player_modals.js]
 ├── fetchMatches(playerId)                          [player_api.js]
 ├── getTournamentNameById(id, tournaments) ⚠️ BUG   [REFERENCIA PERDIDA]
 │   └── Se eliminó del template en PR #2 (#280328d) con nota "moved to player_utils.js"
 │   └── NUNCA se agregó a player_utils.js
 │   └── IMPACTO: openEditMatchModal() lanza ReferenceError
 │
 ├── loadPartnerPlayers()                            [template inline]
 │   └── → fetchAllPlayers()                         [player_api.js]
 │
 ├── lockPartnerForTournament(name)                  [template inline]
 ├── toggleTorneo()                                  [template inline]
 └── DOM writes (20+ elementos del formulario)

deleteMatch(matchId)                                 [template inline, line 1371]
 ├── apiDeleteMatch(matchId, playerId)               [player_api.js]
 ├── loadMatches()                                   [template inline]
 └── renderComputedStats(playerId)                   [template inline]
```

## 2. Side Effects Inventory

| Side Effect | Location | Type |
|------------|----------|------|
| `document.getElementById()` reads (inputs) | saveMatch ~20 reads | DOM read |
| `document.getElementById()` writes (error display) | saveMatch ~5 writes | DOM write |
| `document.getElementById()` writes (form fields) | openEditMatchModal ~15 writes | DOM write |
| `state.matches` read | saveMatch (tournament validation rules) | State read |
| `state.matches` mutated | renderMatches() via loadMatches() | State write |
| `state.tournaments` read | getTournamentNameById() (BUG — no disponible) | State read |
| `state.playerId` read (via `playerId` global) | saveMatch, openEditMatchModal, deleteMatch | State read |
| `localStorage.getItem('access_token')` → `token` | saveMatch (via `deleteMatch`/`saveMatch`) | Auth read |
| `showToast` | deleteSelectedTournament (for delete) | UI |
| `confirm()` dialog | saveMatch (fecha muy antigua), deleteMatch | User prompt |
| `alert()` | openEditMatchModal (error cases) | User prompt |
| `fetch()` → API | saveMatch/updateMatch/deleteMatch via API module | Network |
| `console.log/warn/error` | Multiple points | Debug |

## 3. Branch Analysis

### 3.1 Tipo de Partido

| Branch | Trigger | Path |
|--------|---------|------|
| **Amistoso** | `m-tipo === 'amistoso'` | rival ← `m-rival.value`. tournamentId = null, ronda = null |
| **Torneo** | `m-tipo === 'torneo'` | rival ← `m-pareja-rival.value`. tournamentId ← `m-torneo-select.value`. ronda ← `m-ronda.value` |

### 3.2 Modo de operación

| Branch | Trigger | API Call |
|--------|---------|----------|
| **POST** (crear) | `btn.dataset.matchId` vacío | `apiSaveMatch(playerId, body)` |
| **PUT** (editar) | `btn.dataset.matchId` presente | `updateMatch(matchId, playerId, body)` |

### 3.3 Validaciones (orden de ejecución)

| Step | Condición | Error | Bloqueante |
|------|-----------|-------|:----------:|
| 1 | tipo = torneo && !tournamentId | "Selecciona un torneo" | ✅ |
| 2 | rival.length > 200 | "Nombre muy largo" (OWASP) | ✅ |
| 3 | !rival \|\| !resultado | "Rellena el rival y el resultado" | ✅ |
| 4 | hasLesionNote (⚠️ BUG: ReferenceError) | — | ✅ |
| 5 | validateResultString(resultado) inválido | Mensaje del validador | ✅ |
| 6 | winner mismatch | "El resultado no indica..." | ✅ |
| 7 | Torneo: derrota en ronda inferior | "Ya perdió en {ronda}" | ✅ |
| 8 | Torneo: derrota con wins en rondas superiores | "Hay partidos ganados..." | ✅ |
| 9 | Torneo: ronda duplicada | "Ya existe un partido en {ronda}" | ✅ |
| 10 | Fecha futura | "No puede ser posterior a hoy" | ✅ |
| 11 | Fecha muy antigua (< 2 años) | confirm() dialog | No (aviso) |
| 12 | API error | catch → "Error de conexión" | No |

### 3.4 Resultado

| Outcome | Actions |
|---------|---------|
| **Éxito POST** | closeMatchModal(), reset btn, loadMatches(), renderComputedStats() |
| **Éxito PUT** | closeMatchModal(), reset btn, loadMatches(), renderComputedStats() |
| **Error HTTP** | Display error from API response |
| **Error red** | "Error de conexión" genérico |
| **ReferenceError** (BUG) | `hasLesionNote` / `getTournamentNameById` not defined |

## 4. DOM Dependencies

### Elementos leídos por saveMatch()

| ID | Tipo | Propósito |
|----|------|-----------|
| `m-tipo` | select | Tipo de partido (amistoso/torneo) |
| `m-resultado` | input | String resultado (ej: "6-4 6-3") |
| `m-ganado` | select | Victoria/Derrota |
| `m-match-error` | div | Display de errores |
| `m-torneo-select` | select | Torneo seleccionado |
| `m-pareja-rival` | input | Pareja rival (en torneo) |
| `m-ronda` | select | Ronda del torneo |
| `m-rival` | input | Rival (en amistoso) |
| `m-notas` | textarea | Notas del partido |
| `m-date` | input | Fecha del partido |
| `m-scoring` | select | Sistema de puntuación |
| `m-partner-select` | select | Compañero seleccionado |
| `m-partner-name` | input | Compañero (texto libre) |
| `btn-save-match` | button | Botón guardar (dataset.matchId + texto) |

### Elementos modificados por saveMatch()

| ID | Acción |
|----|--------|
| `match-error` | .textContent + .classList (show/hide) |
| `btn-save-match` | .textContent, .disabled, .dataset.matchId |

## 5. State Dependencies

```
state.matches         → leído por validaciones de torneo (reglas 7, 8, 9)
state.tournaments     → leído por getTournamentNameById (BUG: no disponible)
state.playerId        → leído por API calls (playerId global)
```

## 6. API Dependencies

| Función | API | Método |
|---------|-----|--------|
| `saveMatch()` POST | `/api/v1/players/{id}/matches` | POST |
| `saveMatch()` PUT | `/api/v1/players/{id}/matches/{id}` | PUT |
| `deleteMatch()` | `/api/v1/players/{id}/matches/{id}` | DELETE |
| `loadMatches()` | `/api/v1/players/{id}/matches` | GET |
| `renderComputedStats()` | `/api/v1/players/{id}/stats` | GET |
| `loadPartnerPlayers()` | `/api/v1/players/` | GET |

---

## 7. Bugs Found

### Bug #1: `hasLesionNote()` — función faltante

- **Origen**: PR #2 (#280328d) — se eliminó del template con nota "moved to player_utils.js"
- **Realidad**: Nunca se agregó a player_utils.js
- **Impacto**: saveMatch() lanza ReferenceError en la validación de lesión (línea 697)
- **Firma original**: `function hasLesionNote(notes) { return (notes || '').toLowerCase().match(/lesi[oó]n|retiro|retirada|abandono/i); }`
- **Fix**: Agregar a player_utils.js como función pura (0 side effects, 0 DOM)

### Bug #2: `getTournamentNameById()` — función faltante

- **Origen**: PR #2 (#280328d) — se eliminó del template con nota "moved to player_utils.js"
- **Realidad**: Nunca se agregó a player_utils.js
- **Impacto**: openEditMatchModal() lanza ReferenceError (línea 1298). match_renderer.js también la llama (línea 32) pero con parámetro extra `state.tournaments`
- **Firma necesaria**: `function getTournamentNameById(id, tournaments) { if (!id || !tournaments) return ''; const t = tournaments.find(t => t.id == id); return t ? t.name : ''; }`
- **Nota**: La firma original solo recibía `id` y usaba `loadedTournaments` global. La versión necesitada recibe `(id, tournaments)` con `state.tournaments`
- **Fix**: Agregar a player_utils.js como función pura con la firma actualizada

---

## 8. Orden de Extracción Propuesto

```
Paso 1: Fix bugs — agregar hasLesionNote() y getTournamentNameById() a player_utils.js
Paso 2: Extraer validateResultString() → player_matches.js (pura, 0 side effects)
Paso 3: Extraer renderComputedStats() → player_matches.js (solo DOM writes, sin fetch)
Paso 4: Extraer saveMatch() → player_matches.js (toda la lógica + side effects)
Paso 5: Extraer openEditMatchModal() → player_matches.js (form population)
Paso 6: Extraer deleteMatch() → player_matches.js (API call + refresh)
Paso 7: Eliminar funciones originales del template
Paso 8: UAT completa (crear, editar, eliminar partido; CRUD torneo)
```

> **Nota**: `resetMatchForm()`, `toggleTorneo()`, `onPartnerSelect()`, `lockPartnerForTournament()`, `unlockPartnerSection()`, y las funciones de torneo (showNewTournamentForm, cancelNewTournament, createTournamentInline, etc.) también deberían migrarse a player_matches.js ya que pertenecen al lifecycle de match CRUD.
