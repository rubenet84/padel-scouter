from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
from app.api.v1.auth import router as auth_router
from app.api.v1.players import router as players_router
from app.api.v1.analysis import router as analysis_router
from app.api.v1.views import router as views_router

app = FastAPI(
    title="Padel Scouter API",
    description="Sistema de análisis inteligente de jugadores de pádel con IA",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Archivos estáticos
app.mount("/static", StaticFiles(directory="app/static"), name="static")

# Routers API
app.include_router(auth_router, prefix="/api/v1")
app.include_router(players_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")

# Vistas HTML (al final para no interferir con la API)
app.include_router(views_router)


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}