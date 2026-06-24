from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.api.v1.auth import router as auth_router

app = FastAPI(
    title="Padel Scouter API",
    description="Sistema de análisis inteligente de jugadores de pádel con IA",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/api/v1")


@app.get("/health")
def health():
    return {"status": "ok", "version": "1.0.0"}