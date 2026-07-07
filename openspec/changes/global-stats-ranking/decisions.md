# Decisiones arquitectónicas — global-stats-ranking

## ADR-001: Método DDR (Domain-Driven Refactor)

**Contexto**: El archivo `global_stats.py` (1.492 líneas, 9 responsabilidades) necesitaba ser descompuesto en módulos de dominio sin cambiar comportamiento. No existía una metodología definida para hacerlo — el equipo había usado un enfoque "extraer por tamaño" en refactors anteriores.

**Decisión**: Adoptar el método DDR (Domain-Driven Refactor) con las siguientes reglas:

### Reglas del método DDR

1. **Auditar antes de extraer**: Antes de mover cualquier código, hacer un inventario completo del módulo: líneas por función, tabla de volatilidad (frecuencia de cambio), mapa de cohesión (qué funciones o bloques se referencian entre sí), y copias identificadas (código duplicado).

2. **Extraer infraestructura compartida primero**: Los módulos que contienen lógica de datos sin reglas de negocio (queries, FEP) se extraen primero porque no requieren decisiones arquitectónicas.

3. **Extraer solo lo que cumple 2 criterios**:
   - **2+ consumidores**: El código debe ser usado por al menos dos funciones/módulos diferentes.
   - **Es infraestructura, no lógica de negocio**: Queries, cálculos puros, formateo — no políticas de dominio.

4. **No extraer por similitud de código; extraer cuando existe un núcleo semántico compartido**: Dos bloques que se parecen NO son candidatos a extracción. Dos bloques que representan el mismo concepto del dominio SÍ. La diferencia se revela en la auditoría: no son dos algoritmos distintos ni dos copias casuales; existe un núcleo de dominio común y dos extensiones diferentes.

5. **Cada frontera debe tener una única razón de cambio**: Si el módulo cambiaría por dos motivos distintos (ej: cambiar la fórmula FEP Y cambiar el formato de salida), la frontera está mal.

6. **Verificar que la implementación original desaparece por completo** después de cada extracción (`grep` sin residuales).

7. **Cuando ya no hay lógica que extraer, mover fronteras**: Una vez que todas las responsabilidades están en módulos separados, el archivo original se convierte en una fachada de compatibilidad. El último paso es eliminar la fachada y actualizar los consumidores.

### Timeline de aplicación

| Fase | Decisión clave |
|------|----------------|
| Phase 0 | Inventario + volatilidad + cohesión + 8 copias FEP identificadas |
| Batch 1 | Extraer `compute_fep_points()` — infraestructura compartida, 8 consumidores |
| Batch 2 | Extraer `_compute_player_metrics()` — 5 consumidores, infraestructura |
| Batch 3 | Extraer `build_filters()`, `get_players_by_owner()`, `fetch_match_rows()` — 3+ consumidores, infraestructura |
| Batch 4A | `get_global_summary()` — único consumidor pero dominio aislado → mover frontera |
| Batch 4C | `get_comparison()` + `get_h2h()` — fronteras claras |
| Batch 4D | `get_category_details()` — frontera clara |
| Batch 4B | **Auditoría crítica**: comparar métrica a métrica `get_rankings()` inline vs `_compute_player_metrics()`. Diagnóstico: núcleo semántico compartido + enriquecimientos distintos. Se extrae `compute_player_match_metrics()` siguiendo regla #4 |
| Batch 4E | Mover `get_records()`, `get_evolution()`, `get_community_highlights()` |
| Batch 5 | Eliminar fachada `global_stats.py` |

### Resultado

- **9 módulos** en lugar de 1
- **0 código duplicado** (antes: 60+ líneas FEP inline, 60+ líneas metrics inline)
- **Cada módulo tiene UNA razón de cambio**
- **0 regresiones** verificadas por compilación y por UAT

### Lecciones aprendidas

- La auditoría previa (regla #1) fue la decisión más importante de todo el refactor. Sin ella, `get_rankings()` habría sido extraída a `rankings.py` arrastrando 60 líneas duplicadas.
- La regla #4 (núcleo semántico, no similitud de código) es la que diferencia DDR de un refactor mecánico. Se descubrió durante la auditoría de rankings y se formalizó como regla después.
- El Batch 4B (rankings) fue el más riesgoso porque requería una decisión arquitectónica. Todos los demás batches fueron movimiento mecánico de fronteras ya definidas.
- La progresión no fue lineal por tamaño; Batch 4C (comparison, 306 líneas) se extrajo antes que Batch 4B (rankings, 179 líneas) porque comparison no tenía decisiones pendientes.
