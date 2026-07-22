"""
Configuración de la sesión de base de datos SQLAlchemy.

Provee:
- engine: Conexión a PostgreSQL con pool de conexiones.
- SessionLocal: Factory de sesiones para usar en dependencias FastAPI.
- get_db: Dependencia FastAPI que abre/cierra sesión por request.

Configuración del pool:
- pool_pre_ping=True: verifica que la conexión siga viva antes de usarla.
- pool_size=5: hasta 5 conexiones mantenidas abiertas.
- max_overflow=10: hasta 10 conexiones adicionales bajo carga.
- echo=True en development: loguea todas las queries SQL.
"""
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
    """Dependencia FastAPI — abre y cierra sesión por request.

    Uso:
        @router.get("/")
        def endpoint(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()