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
- 📊 [Presentación (Slides)](#)
- 🎥 [Vídeo demostración](#)
- 🌐 [Despliegue en producción](https://padel-scouter-production.up.railway.app)
- 👤 **Usuario de prueba:** `Ruben829@msn.com` / `Eroseros_1984`

[![Python](https://img.shields.io/badge/Python-3.14+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.138-009688.svg)](https://fastapi.tiangolo.com/)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-336791.svg)](https://www.postgresql.org/)
[![Redis](https://img.shields.io/badge/Redis-7-DC382D.svg)](https://redis.io/)
[![Tests](https://img.shields.io/badge/tests-68%20passed-brightgreen.svg)](tests/)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

---

## 📑 Índice

1. [Descripción del proyecto](#1--descripción-del-proyecto)
2. [Características principales](#2--características-principales)
3. [Stack tecnológico](#3--stack-tecnológico)
4. [Arquitectura](#4--arquitectura)
5. [Estructura del proyecto](#5--estructura-del-proyecto)
6. [Instalación](#6--instalación)
7. [Variables de entorno](#7--variables-de-entorno)
8. [Ejecución](#8--ejecución)
9. [API](#9--api)
10. [Seguridad](#10--seguridad)
11. [Testing](#11--testing)
12. [Capturas](#12--capturas)
13. [Futuras mejoras](#13--futuras-mejoras)
14. [Autor](#14--autor)

---

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
| Cobertura de tests automatizados | ✅ |
| Documentación profesional lista para portfolio | ✅ |

---

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

- **Ranking FEP**: sistema de puntos ponderados por mejor ronda alcanzada en cada torneo
- **Power Level**: puntuación compuesta (0–9999) que integra técnica (45%), físico (25%), mental (20%) y rendimiento competitivo (10%)
- **Clasificación automática** por categoría según Power Level
- **Evolución temporal**: gráficos de progresión de puntos FEP y balance mensual de victorias/derrotas
- **Comparador**: estadísticas lado a lado entre dos jugadores
- **Historial H2H**: enfrentamientos directos con detalle de sets y juegos
- **Top 10**: rankings por puntos, victorias, % victorias, partidos, torneos ganados, finales, semifinales, sets, juegos y racha
- **Récords**: mejor jugador en cada métrica
- **Resumen global**: totales agregados, líder del ranking y mejor porcentaje de victorias
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
- **Estadísticas globales** con rankings, comparador, H2H, récords y highlights
- **Chatbot widget** flotante accesible desde cualquier página autenticada
- **Diseño responsive** con sidebar colapsable en móvil
- **Modales** interactivos para crear/editar jugadores, añadir partidos y confirmar eliminaciones

---

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
│   │   └── summary_service.py
│   │
│   ├── domain/               # Capa de dominio (lógica de negocio pura)
│   │   ├── entities/         #   Entidades: Player, PlayerStats, Tournament, Analysis
│   │   ├── value_objects/    #   Value objects: PowerLevel, FEP, Rounds, Score, Metrics
│   │   └── use_cases/        #   Casos de uso: AnalyzePlayer
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
│   │   ├── partials/         #   Componentes reutilizables
│   │   └── pdf/              #   Plantilla del informe PDF
│   └── static/               # Archivos estáticos (CSS, JS, imágenes)
│       ├── css/
│       ├── js/
│       └── avatars/          #   Avatares subidos por usuarios
│
├── tests/
│   ├── unit/                 # Tests unitarios (7 archivos, 68 tests)
│   ├── integration/          # Tests de integración con BD
│   └── e2e/                  # Tests end-to-end
│
├── alembic/                  # Migraciones de base de datos (16 versiones)
├── data/                     # Datos estáticos (índice RAG)
├── docker-compose.yml        # Servicios Docker (PostgreSQL + Redis)
├── pyproject.toml            # Dependencias y configuración
├── requirements.txt          # Dependencias (pip)
├── .env.example              # Variables de entorno de ejemplo
└── README.md                 # Este documento
```

---

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

Todas las variables de entorno de la [sección 7](#7--variables-de-entorno) deben configurarse en el panel de Secrets del proveedor elegido. Para el comando de inicio en producción:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 4
```

---

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

#### IA

| Método | Ruta | Descripción |
|---|---|---|
| `POST` | `/api/v1/analysis/{player_id}` | Analizar jugador con IA |
| `GET` | `/api/v1/analysis/{player_id}` | Historial de análisis |
| `POST` | `/api/v1/chatbot/ask` | Preguntar al chatbot |

---

## 10. 🛡️ Seguridad

El proyecto implementa protecciones alineadas con el **OWASP Top 10**:

| Control | Implementación |
|---|---|
| **A01 — Broken Access Control** | Verificación de propiedad (`owner_id`) en cada endpoint de jugador, partido y torneo |
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

---

## 11. 🧪 Testing

```bash
# Ejecutar todos los tests unitarios
pytest tests/unit/ -v

# Con cobertura
pytest tests/unit/ --cov=app --cov-report=html

# Tests específicos
pytest tests/unit/test_power_level.py -v
pytest tests/unit/test_security.py -v
```

### Cobertura actual

- **Tests unitarios**: 68 tests (68/68 passed)
- **Tests de integración**: estructura preparada (requiere base de datos)
- **Cobertura de código**: 82%

### Áreas testeadas

| Módulo | Archivo de test | Tests |
|---|---|---|
| Power Level | `test_power_level.py` | 11 |
| Score Rules | `test_score_rules.py` | 15 |
| Security (JWT + passwords) | `test_security.py` | 10 |
| Password Validation | `test_password_validation.py` | 8 |
| AI Analysis | `test_analyze_player.py` | 11 |
| Golpe Definitivo | `test_golpe_definitivo.py` | 12 |
| Classify Player | `test_classify_player.py` | — |

---

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

## 13. 🔮 Futuras mejoras

- [ ] **Internacionalización (i18n)**: soporte multi-idioma (inglés, francés, italiano)
- [ ] **Roles avanzados**: entrenador, jugador, admin con permisos granulares
- [ ] **Notificaciones en tiempo real**: WebSockets para alertas instantáneas
- [ ] **Importación masiva**: CSV/Excel de jugadores y partidos
- [ ] **Panel de administración**: gestión de usuarios, estadísticas globales del sistema
- [ ] **Tests E2E**: escenarios completos con Playwright o Selenium
- [ ] **CI/CD**: GitHub Actions para tests automáticos, linting y despliegue
- [ ] **APP móvil**: PWA o app nativa con React Native
- [ ] **Gamificación**: niveles de experiencia, logros semanales, leaderboards sociales
- [ ] **Historial H2H real**: referenciar rivales como jugadores registrados (`rival_id` FK), permitiendo enfrentamientos directos verificables entre jugadores de la plataforma
- [ ] **Integración con APIs externas**: Federación de Pádel, torneos oficiales

---

## 14. 👨‍💻 Autor

**Rubén Rebollo Rua**

- 📧 [Ruben829@msn.com](mailto:Ruben829@msn.com)
- 💻 [github.com/rubenet84](https://github.com/rubenet84)
- 🎓 Máster en Ingeniería de Software
- 📅 2026

---

<p align="center">
  <sub>Built with ❤️ using Python, FastAPI, and Clean Architecture</sub>
</p>
