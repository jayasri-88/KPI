import logging
from typing import Generator
from sqlalchemy import create_engine, text
from sqlalchemy.orm import DeclarativeBase, sessionmaker, Session

from app.core.config import settings

logger = logging.getLogger("retail_kpi.database")

# Create SQLAlchemy Engine
# Note: For cloud-hosted pooled PostgreSQL (such as Neon pooler), pool_pre_ping=True
# ensures idle severed connections are automatically refreshed, and pool_recycle
# prevents stale sockets.
engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=300,
    echo=(settings.environment == "development" and settings.debug),
)

# SessionLocal class factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


# Modern SQLAlchemy 2.0 Declarative Base
class Base(DeclarativeBase):
    """Base class for all SQLAlchemy ORM models."""
    pass


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency that yields a SQLAlchemy database session per request
    and guarantees closure upon request completion.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def enable_postgis() -> dict:
    """Ensure the PostGIS extension is enabled in PostgreSQL."""
    try:
        with engine.connect() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
            conn.commit()
            postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
            logger.info("PostGIS extension confirmed active: %s", postgis_ver)
            return {"status": "enabled", "version": postgis_ver}
    except Exception as e:
        logger.error("Failed to enable/verify PostGIS: %s", e)
        return {"status": "error", "error": str(e)}


def check_db_connection() -> dict:
    """
    Diagnostic function to test PostgreSQL and PostGIS availability.
    Returns status and version strings.
    """
    try:
        with engine.connect() as conn:
            pg_ver = conn.execute(text("SELECT version();")).scalar()
            # Check PostGIS
            postgis_ver = None
            try:
                postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
            except Exception:
                # Extension might not be loaded yet, attempt to create
                conn.rollback()
                conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
                conn.commit()
                postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()

        return {
            "status": "connected",
            "postgresql": pg_ver,
            "postgis": postgis_ver,
            "details": "PostgreSQL and PostGIS are operational",
        }
    except Exception as e:
        return {
            "status": "disconnected",
            "postgresql": None,
            "postgis": None,
            "details": str(e),
        }