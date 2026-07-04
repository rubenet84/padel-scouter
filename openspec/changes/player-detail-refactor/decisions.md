# Architecture Decision Records — player-detail-refactor

Solo decisiones arquitectónicas importantes. Cada ADR tiene contexto, decisión y consecuencia.

---

## ADR-001: Static assets convention

**Contexto**: Al extraer el CSS inline a `player_detail.css`, se usó `url_for('static', filename='...')` pero Starlette espera `path` como parámetro, no `filename`, y el proyecto existente usa rutas directas `/static/...`.

**Decisión**: Usar ruta directa `/static/css/player_detail.css` en lugar de `url_for`.

**Consecuencias**:
- Consistente con `base.html` y `global_stats.html` que usan `/static/css/scouter.css` y `/static/js/global_stats.js`
- Sin dependencia de route naming de Starlette
- Si se migra a CDN en el futuro, el cambio es buscar y reemplazar

---

## ADR-002: Module access control

**Contexto**: Se definieron 14 módulos en 3 capas (Core, Rendering, Features). Sin reglas de acceso, los módulos pueden acoplarse entre sí.

**Decisión**: Cada capa tiene permiso restringido documentado formalmente en la tabla de acceso del diseño (design.md §3). Core no toca DOM, Rendering no llama API, Features puede hacer ambas.

**Consecuencias**:
- Las code reviews pueden verificar la tabla de acceso contra el código
- Si un módulo viola su capa, se rechaza el PR
- Más boilerplate de paso de dependencias, pero arquitectura explícita

---

## ADR-003: Entry point pattern

**Contexto**: Sin un punto de entrada único, los módulos empezarían a importarse entre sí creando dependencias cruzadas.

**Decisión**: `player_detail.js` es el único archivo que llama a `init*()`. Los módulos no se conocen entre sí — solo `player_detail.js` orquesta.

**Consecuencias**:
- Dependencias explícitas y visibles en un solo lugar
- Para entender el flujo de inicio, solo hay que leer `player_detail.js`
- Los módulos pueden testearse de forma aislada

---

## ADR-004: DOM centralized in player_dom.js

**Contexto**: `document.getElementById(...)` aparecía ~60 veces en el código. Si un id del HTML cambiaba, había que encontrar y actualizar cada ocurrencia.

**Decisión**: Todos los `document.getElementById(...)` viven en `player_dom.js` dentro de un `Object.freeze({...})`. El resto del código referencia `DOM.nombre`.

**Consecuencias**:
- Un solo punto de cambio si un id del HTML se modifica
- `Object.freeze()` evita reasignaciones accidentales
- Fácil de mockear en tests

---

## ADR-005: Feature branch chain strategy

**Contexto**: Se necesitaba decidir cómo entregar 10 PRs secuenciales contra el mismo archivo. Stacked-to-main vs feature branch chain.

**Decisión**: Feature branch chain. Todos los PRs apuntan a `refactor/player-detail`. Solo al final del refactor se mergea la rama a `main`.

**Consecuencias**:
- `main` permanece estable durante todo el refactor
- Si se necesita cambiar algo de un PR anterior, se puede sin contaminar `main`
- Más rebases, pero más seguridad en una operación delicada

---

## ADR-006: Golden rule — never refactor blindly

**Contexto**: En un refactor de 3.619 líneas con lógica acumulada durante meses, hay código que no se entende completamente al leerlo.

**Decisión**: Si durante un PR aparece una función con lógica no documentada o comportamiento ambiguo, se detiene el trabajo, se documenta y se deja para un PR posterior. Nunca se refactoriza "a ciegas".

**Consecuencias**:
- El refactor avanza más lento pero con cero regresiones por código mal entendido
- Se genera documentación de código ambiguo como subproducto
- Los PRs problemáticos se identifican temprano
