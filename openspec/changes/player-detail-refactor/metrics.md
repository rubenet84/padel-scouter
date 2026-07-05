# Metrics — player-detail-refactor

Evolución de métricas por PR. Actualizar al finalizar cada PR.

## Tabla de evolución

| # | PR | player_detail.html | JS inline | CSS inline | Función más larga | Func. >100 | Func. >50 | Código dup. | Globales |
|:-:|----|:------------------:|:---------:|:----------:|:-----------------:|:----------:|:---------:|:-----------:|:--------:|
| — | Inicial | 3.619 | 2.343 | 210 | 239 | 5 | 16 | 131 | 24 |
| 1 | **PR #1 — CSS** | → 3.410 | 2.343 | → **0** | 239 | 5 | 16 | 131 | 24 |
| 2 | **PR #2 — Dead Code + Utils** | 3.335 | 2.269 | 0 | 239 | 5 | 16 | 111 | 24 |
| 3 | **PR #3 — State + DOM + Entry** | 3.069 | 2.004 | 0 | 239 | 5 | 16 | 111 | **8** |
| 4 | **PR #4 — Radar + Power** | 2.810 | 1.727 | 0 | 104 | 1 | 15 | 96 | 8 |
| 5 | **PR #5 — Modals + Search** | 2.606 | 1.524 | 0 | 104 | 1 | 15 | 96 | 6 |
| 6A | **PR #6A — Core Render** | **2.444** | **1.363** | 0 | **105** | **1** | **14** | 96 | **5** |
| 6B | PR #6B — Match Rendering | | | | | | | | |
| 7 | PR #7 — API + Partials | | | | | | | | |
| 8A | PR #8A — Match CRUD | | | | | | | | |
| 8B | PR #8B — Analytics | | | | | | | | |
| — | **Objetivo** | **<700** | **0** | **0** | **<100** | **0** | **—** | **0** | **0** |

> El objetivo <700 líneas es referencia, no mandato. La métrica real es que cada archivo tenga responsabilidad única y cohesionada.

## Detalle por PR

### PR #1 — CSS Extraction

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 3.619 | 3.410 | **−209** |
| CSS inline | 210 | 0 | **−210** |
| JS inline | 2.343 | 2.343 | 0 |
| Función más larga | 239 | 239 | 0 |
| Funciones >100 líneas | 5 | 5 | 0 |
| Funciones >50 líneas | 16 | 16 | 0 |
| Código duplicado | 131 | 131 | 0 |
| Globales | 24 | 24 | 0 |
| `document.getElementById()` | ~60 | ~60 | 0 |

### PR #2 — Dead Code + Utils

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 3.410 | 3.335 | **−75** |
| JS inline | 2.343 | 2.269 | **−74** |
| CSS inline | 0 | 0 | 0 |
| **player_utils.js (nuevo)** | — | **82** | **+82** |
| Función más larga | 239 | 239 | 0 |
| Funciones >100 líneas | 5 | 5 | 0 |
| Funciones >50 líneas | 16 | 16 | 0 |
| Globales | 24 | 24 | 0 |
| `document.getElementById()` | ~60 | ~60 | 0 |

### PR #3 — State + Entry Point + DOM

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 3.335 | **3.069** | **−266** |
| JS inline | 2.269 | **2.004** | **−265** |
| player_state.js (nuevo) | — | **22** | +22 |
| player_constants.js (nuevo) | — | **22** | +22 |
| player_dom.js (nuevo) | — | **153** | +153 |
| player_detail.js (nuevo) | — | **33** | +33 |
| Función más larga | 239 | 239 | 0 |
| Funciones >100 líneas | 5 | 5 | 0 |
| Globales | 24 | **8** | **−16** |
| `document.getElementById()` | ~60 | ~60 | 0 |

> **Nota**: player_dom.js NO está conectado todavía. Se usará a partir de PR #6. Los 153 lines son infraestructura preparada, no código activo.

### PR #4 — Radar + Power

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 3.069 | **2.810** | **−259** |
| JS inline | 2.004 | **1.727** | **−277** |
| player_radar.js (nuevo) | — | **105** | +105 |
| player_power.js (nuevo) | — | **179** | +179 |
| Función más larga | 239 | **104** | **−135** |
| Funciones >100 líneas | 5 | **1** | **−4** |
| Funciones >50 líneas | 16 | **15** | −1 |
| Globales | 8 | 8 | 0 |
| `document.getElementById()` | ~60 | ~60 | 0 |

> **Nota**: 5 funciones extraídas verbatim sin cambiar una línea de lógica. drawRadar → player_radar.js, animatePower/renderDragonBalls/renderShenron/renderGolpeDefinitivo → player_power.js.

### PR #5 — Modals + Search

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 2.810 | **2.606** | **−204** |
| JS inline | 1.727 | **1.524** | **−203** |
| player_modals.js (nuevo) | — | **118** | +118 |
| player_search.js (nuevo) | — | **113** | +113 |
| Función más larga | 104 | 104 | 0 |
| Funciones >100 líneas | 1 | 1 | 0 |
| Globales | 8 | **6** | **−2** |
| `document.getElementById()` | ~60 | ~60 | 0 |

### PR #6A — Core Render

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 2.606 | **2.444** | **−162** |
| JS inline | 1.524 | **1.363** | **−161** |
| player_render.js (nuevo) | — | **182** | +182 |
| Función más larga | 104 | **105** | +1 |
| Funciones >100 líneas | 1 | 1 | 0 |
| Globales | 6 | **5** | **−1** |
| `document.getElementById()` | ~60 | **~43** | **−17** |

> **Nota**: Primer PR que conecta `player_dom.js`. Las funciones extraídas usan `window.DOM.*` en lugar de `document.getElementById`. 17 llamadas DOM reemplazadas. renderPlayer, setAvatar, uploadAvatar, findStrongestStatFromPlayer y SCOUTER_STAT_FIELDS ahora viven en player_render.js.

### PR #6B — Match + Tournament Rendering (target)

| Métrica | Antes | Después | Δ |
|---------|:-----:|:-------:|:-:|
| player_detail.html | 2.444 | | |
| JS inline | 1.363 | | |
| match_renderer.js (nuevo) | — | | |
| tournament_renderer.js (nuevo) | — | | |
| Plantillas Match Card `<div class="match-card"` | **2** | **1** | **−1** |
| Función más larga | 105 | | |
| Funciones >100 líneas | 1 | | |
| Globales | 5 | | |
| `document.getElementById()` | ~43 | | |

> **Target**: Una única función `renderMatchCard()`. Cero HTML duplicado. tournament_renderer.js sin fetch/CRUD.
