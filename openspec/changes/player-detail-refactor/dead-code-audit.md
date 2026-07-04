# Dead Code Audit — PR #2

> **Estado**: Solo auditoría. Cero líneas eliminadas todavía.
> **Archivo analizado**: `app/templates/player_detail.html` (3.410 líneas tras PR #1)

---

## 1. Variables sin uso

| Variable | Línea | Tipo | Referencias | Acción |
|----------|:-----:|------|:-----------:|--------|
| `analysisData` | 1071 | `let` | 0 (solo declaración) | **eliminar** |
| `pendingTournamentCallback` | 2853 | `let` | 0 (solo declaración) | **eliminar** |

---

## 2. Código CSS muerto

| Elemento | Archivo | Línea | Referencias | Acción |
|----------|---------|:-----:|:-----------:|--------|
| `@keyframes starTwinkle` | `player_detail.css` | 50 | 0 (ningún `animation:` la referencia) | **eliminar** |

---

## 3. Funciones duplicadas

| Función #1 | Línea | Función #2 | Línea | Diferencia | Acción |
|------------|:-----:|------------|:-----:|------------|--------|
| `escapeHtml(str)` | 1576 | `escHtml(str)` | 2704 | Implementación distinta (replace vs DOM) | **unificar**: conservar la versión replace (más rápida, sin DOM) |

**Detalle de la duplicación**:

- `escapeHtml` (l.1576): `return (str ?? '').replace(/&/g,'&amp;').replace(...)` — 2 líneas, funcional, sin dependencia del DOM
- `escHtml` (l.2704): `const div = document.createElement('div'); div.textContent = str; return div.innerHTML;` — 5 líneas, crea nodo DOM, más lenta

**Acción**: Conservar `escapeHtml` (versión replace), eliminar `escHtml` y reemplazar sus 3 usos por `escapeHtml`.

---

## 4. Funciones que existen según el diseño pero NO existen en el código

Las siguientes funciones aparecen en `design.md` como candidatas a `player_utils.js`, pero **no existen como funciones nombradas** en el archivo:

| Función | Estado real |
|---------|-------------|
| `removeAccentAndLowerCase()` | ❌ No existe. La lógica de normalización de texto está inline. |
| `strengthDescription()` | ❌ No existe. La descripción de fortalezas está inline. |
| `findMatchByKey()` | ❌ No existe. La búsqueda por key está inline. |
| `getKeyFromString()` | ❌ No existe. |
| `formatStreak()` | ❌ No existe. El formateo de rachas está inline. |
| `formatDate()` | ❌ No existe. Hay 4 implementaciones inline de formateo de fechas. |
| `formatResult()` | ❌ No existe. El formateo de resultados está inline. |

**Acción para PR #2**: Estas funciones se crearán en `player_utils.js` a partir de las implementaciones inline existentes, NO se migrarán de un lugar a otro.

---

## 5. Utilidades existentes con referencias (se migrarán a `player_utils.js`)

| Función | Línea | Llamadas | Acción |
|---------|:-----:|:--------:|--------|
| `escapeHtml(str)` | 1576 | ~5 usos | **migrar** a player_utils (conservar, eliminar escHtml) |
| `showToast(msg, type)` | 1581 | ~8 usos | **migrar** a player_utils |
| `nivelAmenazaFromScore(score)` | 1315 | 3 usos | **migrar** a player_utils |
| `dragonBallCount(nivel)` | 1322 | 1 uso | **migrar** a player_utils |
| `resolveCategoryKey(categoryValue)` | 1812 | 1 uso | **migrar** a player_utils |
| `getMatchTypeBadge(match)` | 1962 | 2 usos | **migrar** a player_utils |
| `hasLesionNote(notes)` | 1969 | 4 usos | **migrar** a player_utils |
| `getTournamentNameById(id)` | 2740 | 5 usos | **migrar** a player_utils |

---

## 6. Resumen de acciones

| Categoría | Cantidad | Acción |
|-----------|:--------:|--------|
| Variables muertas | 2 | Eliminar declaraciones |
| Código CSS muerto | 1 | Eliminar @keyframes |
| Funciones duplicadas | 1 par | Unificar (conservar escapeHtml, eliminar escHtml) |
| Utilidades a migrar | 8 | Mover a player_utils.js |
| Utilidades a crear | 7 | Crear en player_utils.js desde lógica inline |

---

## 7. Trazabilidad: elemento → acción → PR

Esta tabla se actualiza según se ejecuten los PRs.

| Elemento | Acción | PR | Estado |
|----------|--------|:--:|:------:|
| `analysisData` | Eliminar variable | PR #2 | pendiente |
| `pendingTournamentCallback` | Eliminar variable | PR #2 | pendiente |
| `@keyframes starTwinkle` | Eliminar CSS muerto | PR #2 | pendiente |
| `escHtml` | Eliminar (unificar en `escapeHtml`) | PR #2 | pendiente |
| `escapeHtml` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `showToast` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `nivelAmenazaFromScore` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `dragonBallCount` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `resolveCategoryKey` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `getMatchTypeBadge` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `hasLesionNote` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `getTournamentNameById` | Migrar a `player_utils.js` | PR #2 | pendiente |
| `removeAccentAndLowerCase` | Crear desde lógica inline | PR #2 | pendiente |
| `strengthDescription` | Crear desde lógica inline | backlog | pendiente |
| `findMatchByKey` | Crear desde lógica inline | backlog | pendiente |
| `getKeyFromString` | Crear desde lógica inline | backlog | pendiente |
| `formatStreak` | Crear desde lógica inline | backlog | pendiente |
| `formatDate` | Crear desde lógica inline | backlog | pendiente |
| `formatResult` | Crear desde lógica inline | backlog | pendiente |
