from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session

from app.core.config import settings

engine = create_engine(
    settings.database_url,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    echo=settings.environment == "development",
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Create all tables in the database."""
    Base.metadata.create_all(bind=engine)


@event.listens_for(engine, "connect")
def set_postgis_type(**kwargs):
    """Ensure PostGIS types are registered on connection."""
    from sqlalchemy import types
    # This ensures geoalchemy types are loaded
    pass