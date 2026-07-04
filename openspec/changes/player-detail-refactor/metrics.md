# Metrics — player-detail-refactor

Evolución de métricas por PR. Actualizar al finalizar cada PR.

## Tabla de evolución

| # | PR | player_detail.html | JS inline | CSS inline | Función más larga | Func. >100 | Func. >50 | Código dup. | Globales |
|:-:|----|:------------------:|:---------:|:----------:|:-----------------:|:----------:|:---------:|:-----------:|:--------:|
| — | Inicial | 3.619 | 2.343 | 210 | 239 | 5 | 16 | 131 | 24 |
| 1 | **PR #1 — CSS** | → 3.410 | 2.343 | → **0** | 239 | 5 | 16 | 131 | 24 |
| 2 | **PR #2 — Dead Code + Utils** | → 3.335 | → **2.269** | 0 | 239 | 5 | 16 | 111 | 24 |
| 3 | PR #3 — State + DOM + Entry | | | | | | | | |
| 4 | PR #4 — Radar + Power | | | | | | | | |
| 5 | PR #5 — Modals + Search | | | | | | | | |
| 6A | PR #6A — Core Render | | | | | | | | |
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
