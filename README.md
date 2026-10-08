# 🎾 Padel Scouter

<p align="center">
  <img src="app/static/images/dashboard.png" alt="Padel Scouter Dashboard" width="900">
</p>

**Sistema web inteligente para la gestión, análisis y seguimiento de jugadores y torneos de pádel.**

<p align="center">
  🎓 Trabajo Fin de Máster • FastAPI • Clean Architecture • PostgreSQL • IA con Gemini • RAG • Docker
</p>

**Estado del proyecto:** ✅ Finalizado (Trabajo Fin de Máster 2026)

**Arquitectura:** Clean Architecture (Hexagonal) · FastAPI · PostgreSQL · Redis · Google Gemini · WeasyPrint

**🔗 Recursos TFM:**
- 📊 [Presentación (Slides)](docs/Padel_Scouter_Proyecto_TFM_Desarrollo_Con_IA.pptx)
- 🎥 [Vídeo demostración](https://youtu.be/uglVCCTKinU)
- 🌐 [Despliegue en producción](https://padel-scouter-production.up.railway.app)
- 👤 **Usuario demo (rol jugador):** `demo_jugador@padel-scouter.com` / `DemoJugador2026!136f`
- ⚠️ Emails redirigidos a cuenta personal (sin dominio verificado en Resend)

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Tests](https://img.shields.io/badge/tests-406%20passed-brightgreen.svg)](tests/)

---

## 📑 Índice

1. [Descripción del proyecto](#1-descripción-del-proyecto)
2. [Características principales](#2-características-principales)
3. [Stack tecnológico](#3-stack-tecnológico)
4. [Arquitectura](#4-arquitectura)
5. [Estructura del proyecto](#5-estructura-del-proyecto)
6. [Instalación](#6-instalación)
7. [Variables de entorno](#7-variables-de-entorno)
8. [Ejecución](#8-ejecución)
9. [API](#9-api)
10. [Seguridad](#10-seguridad)
11. [Testing](#11-testing)
12. [Capturas](#12-capturas)
13. [Futuras mejoras](#13-futuras-mejoras)
14. [Autor](#14-autor)

---

<a name="1-descripción-del-proyecto"></a>
## 1. 📖 Descripción del proyecto

### Problema que resuelve

Los clubes de pádel, entrenadores y jugadores amateur carecen de herramientas profesionales para analizar el rendimiento, seguir la evolución de jugadores y gestionar torneos de forma centralizada. Las soluciones existentes son hojas de cálculo improvisadas o software genérico que no entiende las particularidades del pádel: sistema FEP, categorías, rondas de torneo, parejas y reglas de competición.

### ¿Qué es Padel Scouter?

Padel Scouter es una plataforma web completa que permite:

- **Gestionar** jugadores con perfiles detallados (19 estadísticas técnicas, físicas y mentales)
- **Registrar** partidos con validación inteligente de rondas de torneo y bloqueo de parejas
- **Analizar** el rendimiento con inteligencia artificial (Google Gemini), generando informes narrativos y planes de mejora personalizados
- **Ranking** basado en el sistema FEP con estadísticas avanzadas, comparativas y evolución temporal
- **Exportar** informes profesionales en PDF con gráficos, análisis y proyecciones
- **Consultar** el reglamento oficial de pádel mediante un chatbot RAG (Retrieval-Augmented Generation)

### Público objetivo

- Entrenadores y directores técnicos de clubes de pádel
- Jugadores que quieren hacer seguimiento de su evolución
- Organizadores de torneos amateur
- Aficionados al pádel que buscan una herramienta profesional

### Objetivos del proyecto

| Objetivo | Estado |
|---|---|
| Sistema CRUD completo de jugadores, partidos y torneos | ✅ |
| Análisis de rendimiento con inteligencia artificial | ✅ |
| Sistema de ranking FEP con estadísticas avanzadas | ✅ |
| Exportación de informes en PDF | ✅ |
| Chatbot de reglamento con RAG | ✅ |
| Arquitectura limpia, mantenible y escalable | ✅ |
| Seguridad según OWASP Top 10 | ✅ |
| RBAC y panel de administración de usuarios | ✅ |
| Cobertura de tests automatizados | ✅ |
| Documentación profesional lista para portfolio | ✅ |

---

<a name="2-características-principales"></a>
## 2. ⭐ Características principales

### 👥 Gestión de jugadores

- **Perfil completo**: 19 campos de estadísticas (10 técnica, 3 físico, 3 mental, 3 competitivo)
- **Campo de mano**: diestro/zurdo con indicador visual
- **Avatar**: subida de imagen con validación, reencodeo seguro (Pillow), eliminación de metadatos EXIF y renombrado aleatorio
- **Soft delete**: borrado lógico con restauración
- **Categorías FIP**: Iniciación, 5ª, 4ª, 3ª, 2ª, 1ª y Profesional

### 🏆 Gestión de torneos

- **CRUD completo** con validación de duplicados por nombre + fecha
- **Puntos FEP** configurables por torneo
- **Asignación de jugadores** a torneos
- **Renombrado inteligente**: al cambiar el nombre de un torneo, todos los partidos asociados se actualizan automáticamente
- **Protección**: no se puede eliminar un torneo con partidos asociados

### ⚔️ Gestión de partidos

- **Registro de partidos** con rival, ronda, resultado, método de puntuación, compañero y notas
- **Validación de rondas** con 4 reglas de torneo:
  1. Una derrota bloquea partidos en rondas posteriores
  2. Una derrota no puede coexistir con victorias en rondas superiores
  3. No se puede saltar rondas (deben ser consecutivas)
  4. No se puede duplicar una ronda en el mismo torneo
- **Bloqueo de parejas**: el compañero se fija para todo el torneo y se autocompleta
- **Auto-swap**: si un jugador era el compañero en un partido anterior, los roles se intercambian automáticamente
- **Métodos de puntuación**: Con Ventaja, Punto de Oro y Star Point
- **Fechas personalizadas** para cada partido

### 🎖️ Sistema de logros (Badges)

10 insignias desbloqueables que se calculan dinámicamente:

| Insignia | Requisito |
|---|---|
| 🩸 Primera Sangre | 1 partido jugado |
| 🔥 En Racha | 3 victorias consecutivas |
| ⚔️ Imparable | 10 victorias consecutivas |
| ⏳ Veterano | 50 partidos totales |
| 💯 Centenario | 100 partidos totales |
| 🛡️ Invicto | 100% victorias (mín. 3) |
| 🏆 Campeón | 1 torneo ganado |
| 🤖 Máquina | 10 torneos ganados |
| ⚡ Poderoso | Power Level ≥ 5000 |
| 💥 Élite | Power Level ≥ 7500 |

### 📊 Estadísticas avanzadas

- **Alcance personal**: todas las estadísticas, rankings, comparativas y récords se calculan **exclusivamente sobre los jugadores del propio usuario**, para todos los roles (incluido `admin`). Nunca se exponen datos de otros propietarios.
- **Ranking FEP**: sistema de puntos ponderados por mejor ronda alcanzada en cada torneo
- **Power Level**: puntuación compuesta (0–9999) que integra técnica (45%), físico (25%), mental (20%) y rendimiento competitivo (10%)
- **Clasificación automática** por categoría según Power Level
- **Evolución temporal**: gráficos de progresión de puntos FEP y balance mensual de victorias/derrotas
- **Comparador**: estadísticas lado a lado entre dos jugadores propios (solo disponible para roles con el permiso `stats.compare`: entrenador y admin)
- **Historial H2H**: enfrentamientos directos con detalle de sets y juegos, solo entre jugadores propios (solo disponible para roles con el permiso `stats.compare`: entrenador y admin)
- **Top 10**: rankings por puntos, victorias, % victorias, partidos, torneos ganados, finales, semifinales, sets, juegos y racha (sobre los jugadores propios)
- **Récords**: mejor jugador propio en cada métrica
- **Resumen global**: totales agregados del usuario, líder de su ranking y mejor porcentaje de victorias
- **Filtros**: por categoría, temporada, tipo de competición y rango de fechas

### 🤖 Inteligencia Artificial

- **Análisis de jugador** con Gemini 2.5 Flash: descripción épica, fortalezas, debilidades y plan de mejora personalizado en 3 fases con frecuencia de entrenamiento
- **Golpe definitivo**: detección automática del mejor golpe del jugador con puntuación y nivel de amenaza
- **Proyección de Power Level**: estimación de evolución en 8 semanas
- **Chatbot de reglamento**: RAG (Retrieval-Augmented Generation) sobre el PDF oficial de reglas de pádel
- **Respuestas fundamentadas**: el chatbot solo responde con información del reglamento, nunca inventa
- **Caché Redis**: 1 semana de caché para preguntas frecuentes del chatbot, ahorrando cuota de API
- **Degradación graceful**: fallback seguro si la API de Gemini o Redis no están disponibles

### 📄 Exportación PDF

- **Informe profesional** generado con WeasyPrint (HTML + CSS → PDF)
- **Portada**: avatar, Power Level gigante, gráfico radar hexagonal, estadísticas clave y categoría sugerida
- **Análisis IA**: descripción narrativa, plan de mejora en 3 tarjetas, fortalezas, debilidades y proyección
- **Gráficos**: radar SVG de 6 vértices con los golpes principales
- **Avatar**: renderizado desde archivo o iniciales como fallback
- **Footer**: numeración de páginas con diseño circular
- **Tokens de descarga**: JWT de 5 minutos para URLs seguras (sin exponer el token de sesión)

### 🔔 Notificaciones

- **Notificaciones automáticas** al añadir un compañero a un partido
- **Mensaje enriquecido** con badges HTML de resultado y tipo de partido
- **Contador no leídas** para polling ligero
- **Limpieza automática**: solo se conservan las 50 últimas notificaciones

### 🔐 Autenticación y seguridad

- **JWT**: access tokens (30 min) + refresh tokens (7 días) con rotación
- **Password hashing**: bcrypt con 12 rondas
- **Rate limiting**: slowapi con límites por IP (200/día, 50/hora global; 3–5/min en auth)
- **Validación de contraseñas**: mínimo 12 caracteres, mayúscula, minúscula, número y carácter especial
- **Recuperación de contraseña**: email con token firmado de 15 minutos
- **Anti-enumeración**: mensajes genéricos en login y forgot-password
- **Emails**: bienvenida y reset de contraseña vía Resend
- **OWASP Top 10**: protecciones implementadas para A01–A07

### 🖥️ Interfaz de usuario

- **Tema oscuro** con diseño profesional (Dragon Ball Z Scouter)
- **Landing page** con datos de ejemplo y secciones informativas
- **Dashboard** con tarjetas de jugadores, badges y nivel de poder
- **Página de jugador** con pestañas: perfil, estadísticas, partidos, análisis IA, gráficos de evolución y badge guía
- **Estadísticas** con rankings, comparador, H2H, récords y highlights (calculados sobre los jugadores propios)
- **Chatbot widget** flotante accesible desde cualquier página autenticada
- **Diseño responsive** con sidebar colapsable en móvil
- **Modales** interactivos para crear/editar jugadores, añadir partidos y confirmar eliminaciones

### 🛡️ Roles, permisos y ownership

El sistema implementa **RBAC (control de acceso basado en roles) con permisos granulares**, con una única fuente de verdad en `app/domain/authorization/policy.py` y un enfoque **fail-closed** (ante un rol desconocido, sin permisos).

Tres roles, con su alcance de datos y límite de jugadores:

| Rol | Alcance | Límite de jugadores | Permisos destacados |
|---|---|---|---|
| `admin` | `GLOBAL` | ilimitado | Todos los permisos del sistema |
| `entrenador` | `ROSTER` | 25 | Los de `jugador` + `players.restore`, `stats.compare`, `reports.generate`, `reports.download` |
| `jugador` | `OWN` | 2 | CRUD de jugadores y partidos propios, `stats.read`, IA, torneos y notificaciones |

- **Permisos granulares** con nomenclatura `recurso.accion` (27 permisos): `users.*`, `players.*`, `matches.*`, `stats.*`, `ai.*`, `reports.*`, `tournaments.*`, `notifications.*`, `audit.read` y `system.manage`. Los endpoints protegidos usan `require_permission(...)`.
- **Scopes de datos**: `OWN` (solo recursos con `owner_id` propio), `ROSTER` (ámbito del entrenador) y `GLOBAL` (todos los recursos).
- **Ownership** por `players.owner_id`: se asigna **en el servidor** desde el usuario autenticado (el cliente no puede fijarlo) y determina qué jugadores ve cada usuario.
- **Lectura vs. escritura**: el `admin` conserva la **lectura** de jugadores por ID, pero **no puede modificar ni eliminar recursos ajenos**: las operaciones de escritura sobre jugadores, partidos o torneos de otro propietario responden **404** (mismo comportamiento que para cualquier usuario) y no hay bypass por UUID en la API.

### 🧑‍💼 Panel de administración (`/admin/users`)

Área exclusiva del rol `admin` para la administración **global de usuarios** (no de jugadores deportivos):

- **Listado paginado** de usuarios con búsqueda (email/usuario) y filtros por rol y estado.
- **Tarjetas de resumen**: total de usuarios, entrenadores, jugadores y cuentas suspendidas.
- **Gestión de roles** limitada a `jugador` ↔ `entrenador` (nunca se puede ascender a `admin`, ni modificar a otro `admin`, ni el propio rol).
- **Suspender / reactivar cuentas** con confirmación en el modal (no se puede suspender la propia cuenta ni dejar el sistema sin administradores activos). Suspender no borra jugadores ni partidos.
- **Auditoría**: cada cambio real (rol, suspensión, reactivación) se registra en la tabla `audit_log`.

> El **dashboard** y todos los endpoints de **`/stats/*`** son **personales** (solo los jugadores del propio usuario, para todos los roles, incluido `admin`). `/admin/users` es la **única vista global** del sistema, y es de **usuarios**, no de jugadores.

---

<a name="3-stack-tecnológico"></a>
## 3. 🔧 Stack tecnológico

| Capa | Tecnología | Versión |
|---|---|---|
| **Lenguaje** | Python | 3.14+ |
| **Framework** | FastAPI | 0.138 |
| **Servidor** | Uvicorn | 0.50.0 |
| **ORM** | SQLAlchemy | 2.0 |
| **Migraciones** | Alembic | 1.18 |
| **Base de datos** | PostgreSQL | 16 |
| **Caché** | Redis | 7 |
| **Autenticación** | python-jose (JWT) | 3.5 |
| **Hashing** | bcrypt | 5.0 |
| **Validación** | Pydantic v2 + email-validator | 2.13 |
| **IA** | Google Gemini (genai SDK) | 2.10 |
| **PDF** | WeasyPrint | 69 |
| **Imágenes** | Pillow | 11 |
| **Email** | Resend | 2.32 |
| **Rate Limiting** | slowapi | 0.1 |
| **Templates** | Jinja2 | 3.1 |
| **Testing** | pytest + pytest-asyncio + pytest-cov | 9.x |
| **Linting** | ruff + black | 0.15 / 26.5 |
| **Contenedores** | Docker + Docker Compose | — |

---

<a name="4-arquitectura"></a>
## 4. 🏗️ Arquitectura

El proyecto sigue los principios de **Clean Architecture** (Hexagonal) con separación estricta de responsabilidades:

```
┌─────────────────────────────────────────────┐
│                  API Layer                   │
│         (FastAPI routers — HTTP)             │
│            auth, players, stats,             │
│       tournaments, analysis, chatbot         │
└──────────────────┬──────────────────────────┘
                   │
┌──────────────────▼──────────────────────────┐
│              Service Layer                   │
│     (orquestación — lógica de aplicación)    │
│   badges, avatar, ranking, summary,          │
│   comparison, analytics, computed_stats      │
└──────┬───────────────────────┬──────────────┘
       │                       │
┌──────▼──────────┐   ┌───────▼──────────────┐
│  Domain Layer   │   │  Infrastructure      │
│  (lógica pura)  │   │  (repositorios,      │
│  power_level,   │   │   AI, PDF, email,    │
│  fep, rounds,   │   │   cache, DB)         │
│  metrics, score │   │                      │
└─────────────────┘   └──────────────────────┘
```

### Principios aplicados

- **Domain Layer**: 100% libre de dependencias de infraestructura (0 imports de SQLAlchemy). Contiene solo lógica de negocio pura testeable sin base de datos.
- **Service Layer**: orquesta el flujo entre API, repositorios y dominio. Cada servicio tiene una única responsabilidad.
- **Repository Layer**: encapsula todo el acceso a datos. Las queries SQL viven exclusivamente aquí.
- **Dependency Inversion**: los servicios dependen de repositorios (abstracciones), no de la base de datos directamente.
- **Single Responsibility**: cada módulo tiene exactamente una razón para cambiar.

Esta separación facilita el mantenimiento, la escalabilidad y la realización de pruebas unitarias al mantener desacopladas las reglas de negocio de la infraestructura.

---

<a name="5-estructura-del-proyecto"></a>
## 5. 📁 Estructura del proyecto

```
padel-scouter/
├── app/
│   ├── api/v1/               # Routers FastAPI (capa HTTP)
│   │   ├── auth.py           #   Registro, login, refresh, reset password
│   │   ├── players.py        #   CRUD jugadores, matches, badges, avatar, PDF
│   │   ├── tournaments.py    #   CRUD torneos
│   │   ├── stats.py          #   Rankings, comparador, H2H, récords, evolución
│   │   ├── analysis.py       #   Análisis IA y consulta de históricos
│   │   ├── chatbot.py        #   Chatbot RAG de reglamento
│   │   ├── notifications.py  #   Notificaciones (campanita)
│   │   ├── admin.py          #   Panel de administración de usuarios (roles, suspensión)
│   │   └── views.py          #   Vistas HTML (templates)
│   │
│   ├── services/             # Capa de servicios (orquestación)
│   │   ├── badges_service.py
│   │   ├── avatar_service.py
│   │   ├── computed_stats_service.py
│   │   ├── analytics_service.py
│   │   ├── ranking_service.py
│   │   ├── comparison_service.py
│   │   ├── category_service.py
│   │   ├── highlights_service.py
│   │   ├── summary_service.py
│   │   └── access_service.py #   Autorización: scopes, ownership (lectura/escritura) y auditoría
│   │
│   ├── domain/               # Capa de dominio (lógica de negocio pura)
│   │   ├── entities/         #   Entidades: Player, PlayerStats, Tournament, Analysis
│   │   ├── value_objects/    #   Value objects: PowerLevel, FEP, Rounds, Score, Metrics
│   │   ├── use_cases/        #   Casos de uso: AnalyzePlayer
│   │   └── authorization/    #   Política RBAC: roles, permisos y scopes (fail-closed)
│   │
│   ├── infrastructure/       # Capa de infraestructura
│   │   ├── database/         #   Modelos ORM, sesión
│   │   ├── repositories/     #   Acceso a datos (queries SQL)
│   │   ├── ai/               #   Cliente Gemini, RAG
│   │   ├── pdf/              #   Generación de PDFs (WeasyPrint)
│   │   ├── email/            #   Servicio de emails (Resend)
│   │   └── cache/            #   Cliente Redis
│   │
│   ├── core/                 # Configuración, seguridad, dependencias
│   │   ├── config.py         #   Settings (Pydantic)
│   │   ├── security.py       #   JWT, bcrypt, tokens
│   │   ├── dependencies.py   #   Dependencias FastAPI (get_current_user, etc.)
│   │   └── rate_limit.py     #   Rate limiting (slowapi)
│   │
│   ├── schemas/              # Esquemas Pydantic (request/response)
│   ├── templates/            # Plantillas Jinja2 (HTML)
│   │   ├── admin_users.html  #   Panel de administración de usuarios
│   │   ├── partials/         #   Componentes reutilizables
│   │   └── pdf/              #   Plantilla del informe PDF
│   └── static/               # Archivos estáticos (CSS, JS, imágenes)
│       ├── css/
│       ├── js/               #   JavaScript del cliente (incluye admin_users.js)
│       └── avatars/          #   Avatares subidos por usuarios
│
├── tests/
│   ├── unit/                 # Tests unitarios (10 archivos, 118 tests)
│   ├── integration/          # Tests de integración con BD (12 archivos, 288 tests)
│   └── e2e/                  # Tests end-to-end
│
├── alembic/                  # Migraciones de base de datos (19 versiones)
├── data/                     # Datos estáticos (índice RAG)
├── docker-compose.yml        # Servicios Docker (PostgreSQL + Redis)
├── pyproject.toml            # Dependencias y configuración
├── requirements.txt          # Dependencias (pip)
├── .env.example              # Variables de entorno de ejemplo
└── README.md                 # Este documento
```

---

<a name="6-instalación"></a>
## 6. 🚀 Instalación

Existen dos formas de instalar el proyecto:

- **Opción A (Recomendada):** Poetry — gestor oficial del proyecto
- **Opción B:** pip mediante `requirements.txt`

### Requisitos previos

- **Python 3.14+**
- **Poetry 2.x** (recomendado) o **pip**
- **Docker Desktop** (para desarrollo local — levanta PostgreSQL 16 + Redis 7)
- **GTK3 Runtime** (solo Windows, para WeasyPrint: [descargar](https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases))

> **Nota**: El gestor oficial de dependencias del proyecto es **Poetry** (`pyproject.toml` y `poetry.lock`). El archivo `requirements.txt` se incluye únicamente para facilitar la instalación mediante `pip`.

### 1. Clonar el repositorio

```bash
git clone https://github.com/rubenet84/padel-scouter.git
cd padel-scouter
```

### 2. Instalar dependencias

**⭐ Opción A: Poetry (recomendada)**

Poetry gestiona el entorno virtual y las dependencias de forma automática.

```bash
poetry install
poetry shell
```

> Si prefieres no usar `poetry shell`, antepone `poetry run` a los comandos siguientes:
> ```bash
> poetry run alembic upgrade head
> poetry run uvicorn app.main:app --reload --port 8000
> ```

**🔧 Opción B: pip + venv**

Alternativa para entornos donde Poetry no está disponible.

```bash
# Crear y activar entorno virtual
python -m venv .venv

# Linux / macOS:
source .venv/bin/activate
# Windows:
.venv\Scripts\activate

# Instalar dependencias
pip install -r requirements.txt
```

### 3. Configurar variables de entorno

```bash
cp .env.example .env
# Editar .env con tus valores (ver sección 7)
```

### 4. Iniciar PostgreSQL y Redis

```bash
docker compose up -d
```

> Docker Compose se utiliza únicamente para el entorno de desarrollo local, levantando PostgreSQL y Redis. En un despliegue en producción pueden utilizarse servicios gestionados (por ejemplo, Supabase para PostgreSQL y Upstash para Redis), por lo que Docker Compose no es obligatorio.

### 5. Ejecutar migraciones

```bash
alembic upgrade head
```

### 6. Iniciar la aplicación

```bash
uvicorn app.main:app --reload --port 8000
```

El proyecto estará disponible en **http://localhost:8000**

- **API docs (Swagger)**: http://localhost:8000/docs
- **API docs (ReDoc)**: http://localhost:8000/redoc
- **Health check**: http://localhost:8000/health

---

<a name="7-variables-de-entorno"></a>
## 7. 🔐 Variables de entorno

Copia `.env.example` a `.env` y configura las siguientes variables:

| Variable | Descripción | Ejemplo |
|---|---|---|
| `DATABASE_URL` | URL de conexión a PostgreSQL | `postgresql+psycopg2://padel:padel_dev@localhost:5432/padel_scouter` |
| `REDIS_URL` | URL de conexión a Redis | `redis://localhost:6379` |
| `SECRET_KEY` | Clave secreta para firmar JWT (mín. 32 caracteres) | `cambia_esto_por_una_clave_segura_de_32_chars` |
| `ALGORITHM` | Algoritmo de firma JWT | `HS256` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | Duración del access token | `30` |
| `REFRESH_TOKEN_EXPIRE_DAYS` | Duración del refresh token | `7` |
| `GOOGLE_API_KEY` | API Key de Google AI Studio (Gemini) | `AIza...` |
| `RESEND_API_KEY` | API Key de Resend (emails) | `re_...` |
| `APP_URL` | URL base de la aplicación | `http://localhost:8000` |
| `APP_ENV` | Entorno (`development` / `production`) | `development` |
| `ALLOWED_ORIGINS` | Orígenes CORS permitidos | `http://localhost:3000,http://localhost:8000` |

---

<a name="8-ejecución"></a>
## 8. ▶️ Ejecución

### Backend

```bash
# Desarrollo (con hot reload)
uvicorn app.main:app --reload --port 8000

# Producción
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

### Docker (servicios de infraestructura)

```bash
# Iniciar PostgreSQL + Redis
docker compose up -d

# Detener
docker compose down

# Detener y eliminar volúmenes
docker compose down -v
```

### Despliegue en producción

El proyecto está preparado para desplegarse en diferentes proveedores cloud. Una configuración recomendada es:

| Componente | Servicio |
|---|---|
| **Backend (FastAPI)** | [Railway](https://railway.app/) |
| **PostgreSQL** | [Supabase](https://supabase.com/) |
| **Redis** | [Upstash](https://upstash.com/) |
| **Variables de entorno** | Secrets del proveedor |

Todas las variables de entorno de la [sección 7](#7-variables-de-entorno) deben configurarse en el panel de Secrets del proveedor elegido. Para el comando de inicio en producción:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

---

<a name="9-api"></a>
## 9. 📡 API

Documentación interactiva disponible en `/docs` (Swagger UI) y `/redoc`.

### Endpoints principales

#### Autenticación

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/auth/register` | Registrar nuevo usuario |
| `POST` | `/api/v1/auth/login` | Iniciar sesión (JWT) |
| `POST` | `/api/v1/auth/refresh` | Renovar tokens |
| `POST` | `/api/v1/auth/forgot-password` | Solicitar reset de contraseña |
| `POST` | `/api/v1/auth/reset-password` | Restablecer contraseña |
| `GET` | `/api/v1/auth/me` | Perfil del usuario actual |

#### Jugadores

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/players/` | Crear jugador |
| `GET` | `/api/v1/players/` | Listar jugadores |
| `GET` | `/api/v1/players/{id}` | Obtener jugador |
| `PUT` | `/api/v1/players/{id}` | Actualizar jugador |
| `DELETE` | `/api/v1/players/{id}` | Eliminar (soft delete) |
| `PUT` | `/api/v1/players/{id}/restore` | Restaurar jugador |
| `POST` | `/api/v1/players/{id}/avatar` | Subir avatar |
| `GET` | `/api/v1/players/{id}/badges` | Obtener logros |
| `GET` | `/api/v1/players/{id}/evolution` | Datos de evolución |
| `GET` | `/api/v1/players/{id}/analytics` | Analíticas detalladas |
| `POST` | `/api/v1/players/{id}/pdf-token` | Generar token de descarga PDF |
| `GET` | `/api/v1/players/{id}/pdf` | Descargar informe PDF |

#### Partidos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/players/{id}/matches` | Añadir partido |
| `GET` | `/api/v1/players/{id}/matches` | Listar partidos |
| `PUT` | `/api/v1/players/{id}/matches/{match_id}` | Actualizar partido |
| `DELETE` | `/api/v1/players/{id}/matches/{match_id}` | Eliminar partido |

#### Torneos

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/tournaments/` | Crear torneo |
| `GET` | `/api/v1/tournaments/` | Listar torneos |
| `PUT` | `/api/v1/tournaments/{id}` | Actualizar torneo |
| `DELETE` | `/api/v1/tournaments/{id}` | Eliminar torneo |

#### Estadísticas

| Método | Ruta | Descripción |
|---|---|---|
| `GET` | `/api/v1/stats/summary` | Resumen global |
| `GET` | `/api/v1/stats/ranking` | Ranking completo |
| `GET` | `/api/v1/stats/top` | Top 10 por métricas |
| `GET` | `/api/v1/stats/compare/{a}/{b}` | Comparar jugadores |
| `GET` | `/api/v1/stats/h2h/{a}/{b}` | Head-to-head |
| `GET` | `/api/v1/stats/records` | Récords |
| `GET` | `/api/v1/stats/categories` | Estadísticas por categoría |
| `GET` | `/api/v1/stats/evolution` | Evolución de puntos |
| `GET` | `/api/v1/stats/community` | Highlights comunidad |

> Todos los endpoints de `/stats/*` devuelven **únicamente datos de los jugadores del propio usuario** (todos los roles, incluido `admin`).

#### IA

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/analysis/{player_id}` | Analizar jugador con IA |
| `GET` | `/api/v1/analysis/{player_id}` | Historial de análisis |
| `POST` | `/api/v1/chatbot/ask` | Preguntar al chatbot |

#### Administración

Área exclusiva del rol `admin`. Requiere el permiso indicado.

| Método | Ruta | Permiso | Descripción |
|---|---|---|---|
| `GET` | `/api/v1/admin/users` | `users.read` | Listado paginado de usuarios (búsqueda y filtros por rol/estado) |
| `GET` | `/api/v1/admin/users/stats` | `users.read` | Totales de usuarios (admins, entrenadores, jugadores, suspendidos) |
| `GET` | `/api/v1/admin/users/{id}` | `users.read` | Detalle de usuario (sin datos sensibles) |
| `PATCH` | `/api/v1/admin/users/{id}/role` | `users.change_role` | Cambiar rol (`jugador` ↔ `entrenador`) |
| `PATCH` | `/api/v1/admin/users/{id}/status` | `users.suspend` | Suspender o reactivar la cuenta |

---

<a name="10-seguridad"></a>
## 10. 🛡️ Seguridad

El proyecto implementa protecciones alineadas con el **OWASP Top 10**:

| Control | Implementación |
|---|---|
| **A01 — Broken Access Control** | RBAC por permisos granulares (`require_permission`) + verificación de propiedad (`owner_id`) en cada endpoint. El `admin` conserva la lectura pero no puede modificar recursos ajenos (404). |
| **A02 — Cryptographic Failures** | bcrypt (12 rounds), JWT HS256, mensajes genéricos en login |
| **A03 — Injection** | Consultas parametrizadas, validación Pydantic, sanitización UUID |
| **A04 — Insecure Design** | Rate limiting por IP, tokens de descarga separados del token de sesión |
| **A05 — Security Misconfiguration** | CORS configurable, secretos en `.env`, `SecretStr` de Pydantic |
| **A06 — Vulnerable Components** | Pillow con reencodeo y stripping EXIF en avatares |
| **A07 — Identification Failures** | Contraseñas ≥12 caracteres con validación, tokens en body (no URL), reset tokens de 15 min, anti-enumeración |

### Protecciones adicionales

- **Rate limiting**: 200 req/día, 50 req/hora globales; 3–5 req/min en endpoints de auth
- **JWT con rotación**: access tokens (30 min) + refresh tokens (7 días) con tipo (`type: "access"` / `"refresh"`)
- **Download tokens**: JWT específicos de 5 minutos para PDF, sin exponer el token de sesión en URLs
- **Soft delete**: borrado lógico en jugadores con restauración
- **Sanitización HTML**: escape de contenido generado por usuarios en notificaciones
- **Cuentas suspendidas**: `is_active` se consulta en la base de datos en **cada petición** (no en el token), por lo que un usuario suspendido queda bloqueado aunque su access token siga vigente
- **Refresh seguro**: `/auth/refresh` rechaza (401) a usuarios inexistentes o inactivos, sin emitir nuevos tokens
- **Registro con rol fijo**: los usuarios se crean siempre con rol `jugador`; no existe endpoint para autoasignarse `admin` o `entrenador`
- **Anti-enumeración**: login con mensaje genérico; el aviso específico de cuenta suspendida solo se muestra con la contraseña correcta
- **Auditoría**: las acciones de administración (cambio de rol, suspensión, reactivación) se registran en `audit_log`

---

<a name="11-testing"></a>
## 11. 🧪 Testing

```bash
# Ejecutar todos los tests unitarios
pytest tests/unit/ -v

# Con cobertura
pytest tests/unit/ --cov=app --cov-report=html

# Tests de integración (requieren una base de datos en marcha)
pytest tests/integration/ -v

# Tests específicos
pytest tests/unit/test_power_level.py -v
pytest tests/unit/test_security.py -v
```

### Cobertura actual

- **Tests unitarios**: 118 tests (118/118 passed)
- **Tests de integración**: 288 tests (288/288 passed) — requieren una base de datos PostgreSQL en marcha
- **Total**: 406 tests

> La cobertura se puede medir con `pytest tests/ --cov=app --cov-report=term-missing` (requiere la base de datos para los tests de integración).

### Áreas testeadas

| Módulo | Archivo de test | Tipo |
|---|---|---|
| Power Level | `test_power_level.py` | Unitario |
| Score Rules | `test_score_rules.py` | Unitario |
| Security (JWT + passwords) | `test_security.py` | Unitario |
| Password Validation | `test_password_validation.py` | Unitario |
| AI Analysis | `test_analyze_player.py` | Unitario |
| Golpe Definitivo | `test_golpe_definitivo.py` | Unitario |
| Classify Player | `test_classify_player.py` | Unitario |
| Política RBAC y permisos | `test_policy.py`, `test_access_control.py` | Unitario |
| Validación del registro | `test_register_schema.py` | Unitario |
| Ownership y scopes | `test_access_service.py` | Integración |
| RBAC de jugadores | `test_players_rbac.py` | Integración |
| RBAC de partidos | `test_matches_rbac.py` | Integración |
| RBAC de torneos | `test_tournaments_rbac.py` | Integración |
| Estadísticas por propietario | `test_stats_rbac.py` | Integración |
| RBAC de análisis IA | `test_analysis_rbac.py` | Integración |
| RBAC de PDFs | `test_pdfs_rbac.py` | Integración |
| RBAC de chatbot | `test_chatbot_rbac.py` | Integración |
| RBAC de notificaciones | `test_notifications_rbac.py` | Integración |
| Panel de administración y suspensión | `test_admin_users_rbac.py` | Integración |
| Auth e integración general | `test_api.py` | Integración |
| Conexión a base de datos | `test_database.py` | Integración |

---

<a name="12-capturas"></a>
## 12. 📸 Capturas

> **Nota**: Las capturas a continuación son representativas de la interfaz. Para ver el proyecto en funcionamiento, sigue los pasos de instalación.


### Landing Page
![Landing Page](app/static/images/Landing_Page.png)

### Login
![Login](app/static/images/Login.png)

### Dashboard
![Dashboard](app/static/images/dashboard.png)

### Menú
![Menú](app/static/images/Menu.png)

### Perfil del Jugador
![Perfil del Jugador](app/static/images/Perfil_Jugador.png)

### Ranking Global
![Ranking Global](app/static/images/Ranking_Global.png)

### Comparador de Jugadores
![Comparador de Jugadores](app/static/images/Comparador_de_Jugadores.png)

### Análisis IA
![Análisis IA](app/static/images/Análisis_IA.png)

### Chatbot de Reglamento
![Chatbot de Reglamento](app/static/images/Chatbot_de_Reglamento.png)

### Informe PDF
![Informe PDF](app/static/images/Informe_PDF.png)

---

<a name="13-futuras-mejoras"></a>
## 13. 🔮 Futuras mejoras

- [ ] **Internacionalización (i18n)**: soporte multi-idioma (inglés, francés, italiano)
- [x] **Roles avanzados y permisos granulares**: roles `admin`, `entrenador` y `jugador` con permisos por recurso (`recurso.accion`), scopes de datos (`OWN`/`ROSTER`/`GLOBAL`) y ownership por `owner_id`
- [ ] **Notificaciones en tiempo real**: WebSockets para alertas instantáneas
- [ ] **Importación masiva**: CSV/Excel de jugadores y partidos
- [x] **Panel de administración — gestión de usuarios**: listado con búsqueda y filtros, cambio de rol (`jugador` ↔ `entrenador`), suspensión/reactivación de cuentas y auditoría
- [ ] **Catálogo global de jugadores y estadísticas globales del sistema**: vista administrativa sobre todos los jugadores (p. ej. `/admin/players`), hoy inexistente
- [ ] **Revocación de refresh tokens**: invalidación explícita de tokens (hoy no son revocables; la suspensión de la cuenta bloquea su uso)
- [ ] **Asignación real entrenador ↔ jugador**: hoy el "roster" del entrenador equivale a sus propios jugadores (`owner_id`), sin relación explícita de asignación
- [ ] **Decidir el alcance de lectura del `admin`**: evaluar si debe poder leer fichas de jugadores ajenos por ID o si debe restringirse también
- [ ] **Tests E2E**: escenarios completos con Playwright o Selenium
- [ ] **CI/CD**: GitHub Actions para tests automáticos, linting y despliegue
- [ ] **APP móvil**: PWA o app nativa con React Native
- [ ] **Gamificación**: niveles de experiencia, logros semanales, leaderboards sociales
- [ ] **Historial H2H real**: referenciar rivales como jugadores registrados (`rival_id` FK), permitiendo enfrentamientos directos verificables entre jugadores de la plataforma
- [ ] **Integración con APIs externas**: Federación de Pádel, torneos oficiales

### Limitaciones conocidas

- **Refresh tokens no revocables**: no existe una lista de revocación; un refresh token sigue siendo válido hasta su expiración (7 días). La suspensión de la cuenta sí bloquea su uso, porque tanto cada petición como `/auth/refresh` comprueban `is_active` en la base de datos.
- **Roster del entrenador implícito**: el alcance del entrenador (`ROSTER`) equivale hoy a `owner_id == user.id`; no existe una tabla de asignación explícita entrenador ↔ jugador.
- **Lectura del `admin` por ID**: el `admin` conserva la lectura de cualquier jugador por su ID (incluida la ficha `/player/{id}`), aunque no puede modificarlo. Está pendiente decidir si ese acceso debe restringirse.

### Licencia

Código publicado solo para evaluación y portfolio. © 2026 Rubén Rebollo Rua. Todos los derechos reservados. Ver [LICENSE.txt](LICENSE.txt).

---

<a name="14-autor"></a>
## 14. 👨‍💻 Autor

**Rubén Rebollo Rua**

- 📧 [Ruben829@msn.com](mailto:Ruben829@msn.com)
- 💻 [github.com/rubenet84](https://github.com/rubenet84)
- 🎓 Máster en Desarrollo con IA
- 📅 2026

---

<p align="center">
  <sub>Built with ❤️ using Python, FastAPI, and Clean Architecture</sub>
</p>
