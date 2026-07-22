"""
Punto de entrada de la aplicación Padel Scouter.

Configura la instancia de FastAPI con:
- Gestión del ciclo de vida (creación de tablas al iniciar).
- Middleware CORS para permitir peticiones desde el frontend.
- Rate limiting global vía slowapi.
- Montaje de archivos estáticos para avatares y assets.
- Inclusión de todos los routers versionados bajo /api/v1.
- Router de vistas HTML para el frontend server-rendered.

Arquitectura: Capa de aplicación (entry point) — orquesta infraestructura,
API, servicios y dominio sin contener lógica de negocio propia.
"""
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from app.core.config import settings
from app.core.rate_limit import limiter
from app.api.v1.auth import router as auth_router
from app.api.v1.players import router as players_router
from app.api.v1.tournaments import router as tournaments_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.views import router as views_router
from app.api.v1.chatbot import router as chatbot_router
from app.api.v1.stats import router as stats_router
from app.api.v1.notifications import router as notifications_router
from app.infrastructure.database.models import Base
from app.infrastructure.database.session import engine


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Ciclo de vida de la aplicación: crea las tablas al iniciar si no existen.

    Corre sobre el engine configurado en app.infrastructure.database.session.
    En producción, se recomienda usar Alembic para migraciones en lugar de
    create_all automático.
    """
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title="Padel Scouter API",
    description="Sistema de análisis inteligente de jugadores de pádel con IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)


# ── Rate Limit Handler ──────────────────────────────────────────
async def _rate_limit_exceeded_handler(request, exc):
    """Manejador global para excepciones de rate limiting (slowapi).

    Devuelve un 429 con un mensaje en español para mantener consistencia
    con el resto de mensajes de error de la API.
    """
    return JSONResponse(
        status_code=429,
        content={"detail": "Demasiadas peticiones. Esperá un momento."},
    )

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

# Configuración de CORS: orígenes permitidos definidos en settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos (avatares, imágenes, CSS/JS del frontend)
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# ── Routers versionados bajo /api/v1 ────────────────────────────
app.include_router(auth_router, prefix="/api/v1")
app.include_router(players_router, prefix="/api/v1")
app.include_router(tournaments_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(chatbot_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
# Router de vistas HTML sin prefijo (sirve templates directamente)
app.include_router(views_router)


@app.get("/health")
def health():
    """Health check básico para monitoreo y balanceadores de carga."""
    return {"status": "ok", "version": "1.0.0"}