from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.core.config import settings
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
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.include_router(auth_router, prefix="/api/v1")
app.include_router(players_router, prefix="/api/v1")
app.include_router(tournaments_router, prefix="/api/v1")
app.include_router(analysis_router, prefix="/api/v1")
app.include_router(chatbot_router, prefix="/api/v1")
app.include_router(stats_router, prefix="/api/v1")
app.include_router(notifications_router, prefix="/api/v1")
app.include_router(views_router)

@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}