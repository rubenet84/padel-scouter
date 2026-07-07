# Metrics — global-stats-ranking

Evolución del archivo `global_stats.py` durante el refactor DDR. Actualizado al finalizar cada batch.

## Tabla de evolución

| # | Batch | global_stats.py | Módulos extraídos | Función más larga | Código duplicado |
|:-:|-------|:---------------:|:------------------:|:-----------------:|:----------------:|
| — | Inicial | 1.492 | — | 345 (comparison) | 60+ (FEP copy) |
| 1 | **Batch 1 — fep.py** | ~1.400 | 45 | 345 | **0** (FEP unificado) |
| 2 | **Batch 2 — metrics.py** | ~1.300 | 158 | 345 | **0** |
| 3 | **Batch 3 — queries.py** | ~1.200 | 243 | 345 | **0** |
| 4A | **Batch 4A — summary.py** | ~1.100 | 340 | 345 | **0** |
| 4C | **Batch 4C — comparison.py** | ~760 | 646 | 155 (rankings) | **0** |
| 4D | **Batch 4D — categories.py** | ~660 | 741 | 155 (rankings) | **0** |
| 4B | **Batch 4B — rankings.py** | 507 | 920 | 155 (highlights) | **0** |
| 4E | **Batch 4E — highlights.py** | 248 | 1.164 | 155 (highlights) | **0** |
| 5 | **Batch 5 — Eliminación** | **0** | **1.164** | 155 (highlights) | **0** |

## Métricas finales por módulo

| Módulo | Líneas | Responsabilidad |
|--------|:------:|:----------------|
| `fep.py` | 45 | Cálculo de puntos FEP |
| `metrics.py` | 113 | Métricas base + extendidas por jugador |
| `queries.py` | 85 | Queries compartidas (build_filters, fetch_match_rows) |
| `summary.py` | 97 | Resumen global agregado |
| `comparison.py` | 306 | Comparación 1v1 + Head-to-Head |
| `categories.py` | 95 | Stats por categoría |
| `rankings.py` | 179 | Ranking FEP + Top 10 lists |
| `highlights.py` | 244 | Records, evolución, community highlights |
| **Total** | **1.164** | **8 módulos, 1 responsabilidad cada uno** |

## Comparativa inicial vs final

| Métrica | Inicial | Final | Δ |
|---------|:-------:|:-----:|:-:|
| `global_stats.py` | 1.492 | **0** | **−1.492** |
| Módulos de dominio | 1 | **9** | **+8** |
| Responsabilidades por módulo | 9 | **1** (cada uno) | **−8** |
| Código duplicado (FEP inline) | 60+ líneas | **0** | Eliminado |
| Código duplicado (metrics inline) | 60+ líneas | **0** | Eliminado |

## Notas

- La reducción de líneas NO fue el objetivo — fue consecuencia de aplicar DDR correctamente.
- La métrica real de éxito: cada módulo tiene UNA razón de cambio.
- El batch más riesgoso fue 4B (rankings) porque requería la auditoría de `compute_player_match_metrics` antes de mover la frontera.
- `get_community_highlights()` conserva su query propia con `player2_id`/`partner_nombre` — no se unificó porque la variante no tiene 2+ consumidores (DDR regla #4).
