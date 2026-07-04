# player_detail.html — Diseño de refactor

Arquitectura por dominios con un único punto de entrada, sin variables globales y con dependencias explícitas.

> **Contexto**: 3.619 líneas → 210 CSS + 1.066 HTML + 2.343 JS (~70 funciones). Inventario completo en `inventory.md`.

---

## 1. Arquitectura: tres capas por responsabilidad

Cada módulo tiene una **única responsabilidad** y acceso restringido según su capa.

| Capa | Módulos | Responsabilidad |
|------|---------|-----------------|
| **Core** | `player_state`, `player_utils`, `player_api` | Estado, utilidades, comunicación con backend |
| **Rendering** | `player_render`, `match_renderer`, `tournament_renderer` | Solo pintar en el DOM. No llaman a la API. |
| **Features** | `player_matches`, `player_analytics`, `player_search`, `player_radar`, `player_power`, `player_modals` | Orquestan: leen estado, llaman API, renderizan |

```
player_detail.js  (entry point — solo init*())
    │
    ├── Core ─────────────────────────────────┐
    │   ├── player_state.js      (estado)     │
    │   ├── player_utils.js      (utilidades) │
    │   └── player_api.js        (fetch)      │
    │                                          │
    ├── Rendering ────────────────┐            │
    │   ├── player_render.js      │            │
    │   ├── match_renderer.js     │            │
    │   └── tournament_renderer.js│            │
    │                              │            │
    ├── Features ─────────────────┤            │
    │   ├── player_matches.js     │            │
    │   ├── player_analytics.js   │            │
    │   ├── player_search.js      │            │
    │   ├── player_radar.js       │            │
    │   ├── player_power.js       │            │
    │   └── player_modals.js      │            │
    │                              │            │
    └── static/ ──────────────────┘            │
        └── player_detail.css                  │
                                                │
templates/ ────────────────────────────────────┘
    ├── player_detail.html         (layout)
    └── partials/
        ├── player_header.html
        ├── player_matches.html
        ├── player_radar.html
        ├── player_power.html
        ├── player_analytics.html
        └── player_modals.html
```

---

## 2. Catálogo de módulos

### 2.1 Core — `static/js/player_detail/`

#### `player_state.js` — Gestión de estado

Almacena y provee el estado compartido. No toca el DOM ni llama a la API.

**Exporta**: `PlayerState` (clase)

```javascript
const state = new PlayerState();
// state.player, state.matches, state.tournaments, state.players
```

**Funciones que migran aquí**:

| Función original | Líneas |
|-----------------|--------|
| Variables globales (playerId, currentPlayerId, loadedMatches, etc.) | ~15 vars |

#### `player_utils.js` — Utilidades puras

Funciones que no dependen del DOM, estado, ni API. Sin efectos secundarios.

**Funciones que migran aquí**:

| Función original | Líneas |
|-----------------|--------|
| `escapeHtml()` (versión unificada) | 9 |
| `removeAccentAndLowerCase()` | 6 |
| `strengthDescription()` | 23 |
| `findMatchByKey()`, `getKeyFromString()` | ~20 |
| `formatStreak()`, `formatDate()`, `formatResult()` | ~40 |
| `showToast()` (no necesita DOM ref centralizado) | ~15 |

#### `player_api.js` — Comunicación con backend

Todas las llamadas `fetch()`. Sin lógica de presentación.

**Funciones que migran aquí**:

| Función original | Líneas |
|-----------------|--------|
| `saveAndAnalyze()` → parte API | split |
| `loadPlayer()` | 50 |
| `loadMatches()`, `loadMatchHistory()` | 30 |
| `loadTournaments()` | 25 |
| `deleteMatchFromDB()` | 20 |
| `openLevelGuideModal()` → `fetchLevelGuide()` (API pura) | ~10 |

### 2.2 Rendering — `static/js/player_detail/`

#### `player_render.js` — Render principal

Orquesta la renderización de la cabecera, stats, y secciones principales del jugador. **No llama a la API**.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `renderPlayer()` | 93 | 🔴 |
| `renderComputedStats()` | 85 | 🟡 |
| `renderMatchesHeader()` | 25 | 🟢 |
| `renderTabs()` (filtros) | 15 | 🟢 |

#### `match_renderer.js` — Render de partidos

Renderiza el match card, la lista de partidos, y el historial. Contiene la **lógica del template duplicado** que se unificará.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `renderMatches()` | 178 | 🟡 |
| `renderFullMatchHistory()` | 98 | 🟡 |
| `renderMatchCard()` → **NUEVA** (extraída del duplicado) | ~65 | 🟢 |

#### `tournament_renderer.js` — Render de torneos

Renderiza la sección de torneos y el modal de info de torneo.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `renderTournaments()` | 87 | 🟡 |
| `openTournamentInfoModal()` → render | ~20 | 🟢 |

### 2.3 Features — `static/js/player_detail/`

#### `player_matches.js` — CRUD de partidos

Gestiona el ciclo de vida completo de un partido: crear, editar, borrar, validar. Es el módulo **más grande y riesgoso**.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `saveMatch()` | 239 | 🔴🔴 |
| `openEditMatchModal()` | 125 | 🔴 |
| `editMatch()` | 49 | 🟡 |
| `deleteMatch()` | 35 | 🟡 |
| `validateResultString()` | 58 | 🟡 |
| `saveAndAnalyze()` → parte lógica | split | 🟡 |

#### `player_analytics.js` — Analytics de partidos

Gestiona el modal de analytics, obteniendo datos de la API y dibujando el análisis.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `openMatchAnalyticsModal()` | 89 | 🟡 |
| `closeMatchAnalyticsModal()` | 6 | 🟢 |
| `openTournamentInfoModal()` → parte data + render | split | 🟢 |

#### `player_search.js` — Búsqueda y filtros

Gestiona el filtrado de partidos por búsqueda de texto.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `filterMatchesBySearch()` | 22 | 🟢 |
| `filterMatchHistory()` | 15 | 🟢 |

#### `player_radar.js` — Gráfico radar

Dibuja el radar chart de stats. Sin llamadas API.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `drawRadar()` | 80 | 🟡 |
| `drawRadarGrid()`, `drawRadarData()`, etc. (sub-funciones) | split | 🟢 |

#### `player_power.js` — Power Level + Dragon Balls + Golpe Definitivo

Gestiona toda la sección visual de poder.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `animatePower()` | 80 | 🟡 |
| `renderDragonBalls()` | 43 | 🟢 |
| `renderGolpeDefinitivo()` | 31 | 🟢 |
| `renderShenron()` | 11 | 🟢 |
| `openLevelGuideModal()` → parte render | ~15 | 🟢 |

#### `player_modals.js` — Gestión de modales

Abre y cierra modales. Responsabilidad UI pura. El contenido de cada modal se lo pasa el feature module correspondiente.

**Funciones que migran aquí**:

| Función original | Líneas | Riesgo |
|-----------------|--------|--------|
| `openEditModal()`, `closeEditModal()` | ~20 | 🟢 |
| `openStatsModal()`, `closeStatsModal()` | ~30 | 🟢 |
| `openLevelGuideModal()`, `closeLevelGuideModal()` | ~15 | 🟢 |
| Utilidades de overlay/dimmer | ~10 | 🟢 |

### 2.4 Entry point — `player_detail.js`

**Único archivo con lógica de inicialización**. Solo llama a funciones `init*()`. No contiene implementación de features.

```javascript
// player_detail.js
import { PlayerState } from './player_detail/player_state.js';
import { DOM } from './player_detail/player_dom.js';
import { apiFetchPlayer, apiFetchMatches, apiFetchTournaments } from './player_detail/player_api.js';
import { playerRender } from './player_detail/player_render.js';
import { matchRenderer } from './player_detail/match_renderer.js';
import { initRadar } from './player_detail/player_radar.js';
import { initMatches } from './player_detail/player_matches.js';
import { initAnalytics } from './player_detail/player_analytics.js';
import { initSearch } from './player_detail/player_search.js';

const state = new PlayerState();
const dom = DOM;

async function initPlayerDetail(playerId) {
    // 1. Cargar datos
    const [player, matches, tournaments] = await Promise.all([
        apiFetchPlayer(playerId),
        apiFetchMatches(playerId),
        apiFetchTournaments(playerId)
    ]);

    // 2. Poblar estado
    state.player = player;
    state.matches = matches;
    state.tournaments = tournaments;

    // 3. Inicializar subsistemas
    playerRender(dom, state);
    initRadar(dom, state);
    initMatches(dom, state);
    initAnalytics(dom, state);
    initSearch(dom, state);
}

// Arranque
const playerId = dom.playerId?.value;
if (playerId) initPlayerDetail(playerId);
```

---

## 3. Tabla de acceso por módulo

| Módulo | Puede acceder al DOM | Puede llamar API | Puede modificar estado |
|--------|----------------------|------------------|------------------------|
| `player_state` | ❌ | ❌ | ✅ |
| `player_utils` | ❌ | ❌ | ❌ |
| `player_api` | ❌ | ✅ | ❌ |
| `player_render` | ✅ | ❌ | ✅ (solo lectura) |
| `match_renderer` | ✅ | ❌ | ✅ (solo lectura) |
| `tournament_renderer` | ✅ | ❌ | ✅ (solo lectura) |
| `player_matches` | ✅ | ✅ | ✅ |
| `player_analytics` | ✅ | ✅ | ✅ (solo lectura) |
| `player_search` | ✅ | ❌ | ✅ (solo lectura) |
| `player_radar` | ✅ | ❌ | ✅ (solo lectura) |
| `player_power` | ✅ | ❌ | ✅ (solo lectura) |
| `player_modals` | ✅ | ❌ | ❌ |

**Regla**: "solo lectura" significa que el módulo recibe el estado como parámetro y lo lee, pero nunca lo muta directamente.

---

## 4. DOM centralizado — `player_dom.js`

Todos los `document.getElementById(...)` viven aquí. El resto del código referencia `DOM.nombre`.

```javascript
// player_dom.js
export const DOM = Object.freeze({
    // Header
    playerName: document.getElementById('playerName'),
    playerPhoto: document.getElementById('playerPhoto'),
    playerLevel: document.getElementById('playerLevel'),
    playerId: document.getElementById('playerId'),

    // Stats
    statsSection: document.getElementById('statsSection'),

    // Radar
    radarChart: document.getElementById('radarChart'),
    radarLabels: document.getElementById('radarLabels'),
    radarData: document.getElementById('radarData'),

    // Power
    powerContainer: document.getElementById('powerContainer'),
    dragonBallIcons: document.getElementById('dragonBallIcons'),

    // Matches
    matchesSection: document.getElementById('matchesSection'),
    matchHistorySection: document.getElementById('matchHistorySection'),
    matchHistoryDetail: document.getElementById('matchHistoryDetail'),

    // Search
    searchInput: document.getElementById('searchInput'),
    matchHistorySearch: document.getElementById('matchHistorySearch'),

    // Match form
    matchForm: document.getElementById('matchForm'),
    resultString: document.getElementById('resultString'),
    matchDate: document.getElementById('matchDate'),
    tournamentId: document.getElementById('tournamentId'),
    matchIdInput: document.getElementById('matchId'),

    // Modals
    editMatchModal: document.getElementById('editMatchModal'),
    statsModal: document.getElementById('statsModal'),
    analyticsModal: document.getElementById('analyticsModal'),
    levelGuideModal: document.getElementById('levelGuideModal'),
    modalOverlay: document.getElementById('modalOverlay'),

    // Buttons
    saveMatchBtn: document.getElementById('saveMatchBtn'),
    deleteMatchBtn: document.getElementById('deleteMatchBtn'),
    addMatchBtn: document.getElementById('addMatchBtn'),
});
```

**Ventajas**:
- Un solo `document.getElementById(...)` por elemento en toda la app
- Si cambia un `id` en el HTML, solo se actualiza aquí
- `Object.freeze()` evita reasignaciones accidentales

---

## 5. Estructura de archivos final

```
app/
├── static/
│   ├── css/
│   │   └── player_detail.css              ← NUEVO (todo el CSS extraído)
│   │
│   └── js/
│       ├── player_detail.js               ← NUEVO (entry point)
│       │
│       └── player_detail/                 ← NUEVO (todos los módulos)
│           ├── player_state.js
│           ├── player_utils.js
│           ├── player_api.js
│           ├── player_dom.js
│           ├── player_render.js
│           ├── match_renderer.js
│           ├── tournament_renderer.js
│           ├── player_matches.js
│           ├── player_analytics.js
│           ├── player_search.js
│           ├── player_radar.js
│           ├── player_power.js
│           └── player_modals.js
│
└── templates/
    ├── player_detail.html                 ← MODIFICADO (layout que incluye partials)
    │
    └── partials/                          ← NUEVO
        ├── player_header.html
        ├── player_matches.html
        ├── player_radar.html
        ├── player_power.html
        ├── player_analytics.html
        └── player_modals.html
```

---

## 6. Plan de ejecución (8 PRs encadenados)

El orden está diseñado para **repartir riesgo**: módulos independientes primero, features complejas al final.

| PR | Módulos | Archivos nuevos | Líneas estimadas | Riesgo |
|----|---------|-----------------|-----------------|--------|
| **#1** | CSS | `player_detail.css` | ~210 | 🟢 |
| **#2** | Limpieza + Utils | `player_utils.js`, limpiar dead code | ~120 | 🟢 |
| **#3** | Estado + Entry Point + DOM | `player_state.js`, `player_dom.js`, `player_detail.js` | ~150 | 🟢 |
| **#4** | Visuales: Radar + Power | `player_radar.js`, `player_power.js` | ~220 | 🟡 |
| **#5** | Modales + Search | `player_modals.js`, `player_search.js` | ~100 | 🟢 |
| **#6** | Rendering | `player_render.js`, `match_renderer.js`, `tournament_renderer.js` | ~450 | 🟡 |
| **#7** | Infraestructura | `player_api.js`, partials Jinja, adaptar imports | ~300 | 🟡 |
| **#8** | Features | `player_matches.js`, `player_analytics.js` | ~500 | 🔴 |

**Cada PR sigue el ciclo**: Extraer → Integrar → Validar → Eliminar

1. **Extraer** el bloque al nuevo módulo (el código original sigue vivo)
2. **Integrar** el nuevo módulo en el template (import, init, etc.)
3. **Validar** que todo funciona (checklist común + tests)
4. **Eliminar** el código original del archivo grande
5. Solo entonces mergear a `main` y pasar al siguiente PR

Nunca código "a medias" repartido entre dos sitios. Cada PR queda autocontenido.

---

## 7. Reglas del refactor

1. **Refactor puro**: cero cambios de funcionalidad, diseño, textos o comportamiento. Si algo cambia debe ser solo para corregir un bug detectado durante la extracción.
2. **Extraer → Integrar → Validar → Eliminar**: en cada PR, el código antiguo se elimina solo después de validar que el nuevo módulo funciona. Nunca código "a medias".
3. **Dependencias explícitas**: ningún módulo busca datos de `window` o variables globales. Todo se pasa como parámetro.
4. **DOM centralizado**: los `document.getElementById()` solo existen en `player_dom.js`.
5. **Sin fugas**: después del último PR, `player_detail.html` debe tener cero JS inline (solo `{% block scripts %}` incluyendo `player_detail.js`).
6. **Validación post-PR**: comportamiento visual y funcional idéntico al anterior. Si el radar se veía igual, la edición funcionaba igual, los filtros actuaban igual.
7. **Sin archivos >700 líneas**: si un módulo nuevo supera ese umbral, se divide antes de mergear.

---

## 8. Checklist común de validación (todos los PRs)

Cada PR debe pasar este checklist completo antes de mergear.

### Checklist técnico

- [ ] Sin cambios funcionales (refactor puro)
- [ ] Sin cambios visuales (diseño, colores, tamaños, textos idénticos)
- [ ] Sin regresiones conocidas
- [ ] Sin duplicación nueva
- [ ] Sin variables globales añadidas
- [ ] Sin warnings en consola del navegador
- [ ] Sin errores en servidor (uvicorn)

### Checklist de código

- [ ] Ninguna función nueva supera 100 líneas (o justificación documentada)
- [ ] Ningún archivo supera 700 líneas
- [ ] Dependencias documentadas en el módulo
- [ ] Imports ordenados
- [ ] Sin código muerto (ni del original ni nuevo)

### Checklist manual

- [ ] Crear partido
- [ ] Editar partido
- [ ] Eliminar partido
- [ ] Abrir analytics de partido
- [ ] Radar correcto (stats, etiquetas)
- [ ] Power level correcto (dragon balls, golpe)
- [ ] Búsqueda/filtros correcta
- [ ] Modales abren y cierran correctamente

---

## 9. Métricas de progreso

Al finalizar cada PR, se registra esta tabla para medir la mejora objetiva.

| Métrica | Antes | Después | Diferencia |
|---------|:-----:|:-------:|:----------:|
| Líneas `player_detail.html` | 3619 | | |
| JS inline (líneas) | 2343 | | |
| CSS inline (líneas) | 210 | | |
| Funciones >50 líneas | 16 | | |
| Código duplicado (líneas) | 131 | | |
| Variables globales | 24 | | |
| `document.getElementById(...)` | ~60 | | |

No se persigue un número mágico, sino una **mejora visible en cada iteración**.

---

## 10. Checklist de aprobación del diseño

- [ ] La estructura de archivos refleja responsabilidades, no tipos
- [ ] Existe un único punto de entrada (`player_detail.js`)
- [ ] No hay variables globales — todas las dependencias son explícitas
- [ ] Los módulos de Core no tocan el DOM
- [ ] Los módulos de Rendering no llaman a la API
- [ ] Cada módulo de Features orquesta su dominio completo
- [ ] El DOM está centralizado en `player_dom.js`
- [ ] El orden de PRs aísla el riesgo (fáciles primero, complejos al final)
- [ ] Después del refactor, `player_detail.html` queda sin JS inline
- [ ] Todos los PRs usan el mismo checklist común de validación
- [ ] Se registran métricas de progreso al finalizar cada PR

---

## Siguiente paso

Diseño aprobado → paso a **Fase 3 — Tasks**: desglose de tareas individuales por PR con criterios de aceptación y estimación de líneas por archivo.
