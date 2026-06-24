from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_pre_ping=True,       # reconecta si la conexión se cayó
    pool_size=5,
    max_overflow=10,
    echo=settings.app_env == "development",  # log SQL en dev
)

SessionLocal = sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
)


def get_db() -> Session:
    """Dependencia FastAPI — abre y cierra sesión por request."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()