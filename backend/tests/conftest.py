"""Fixtures for analytics service tests.

Runs against the project's PostgreSQL database (DATABASE_URL resolved by
app.core.config), but inside a throwaway schema created once per test
session, so application tables are never touched. The schema is dropped
again on teardown.

The schema is attached explicitly to every Table in the metadata instead
of via search_path, because pooled Neon endpoints reject the search_path
startup parameter. Services are exercised through their real code paths
by pointing their module-level SessionLocal at a session factory bound to
the test engine.
"""

import uuid

import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.database import Base
import app.models  # noqa: F401  (registers all mappers on Base)


@pytest.fixture(scope="session")
def pg_engine():
    schema_name = f"analytics_test_{uuid.uuid4().hex[:12]}"
    engine = create_engine(settings.database_url)

    with engine.connect() as conn:
        conn.execute(text(f'CREATE SCHEMA "{schema_name}"'))
        conn.commit()

    # Fully-qualify every table with the throwaway schema (pooler-safe).
    for table in Base.metadata.tables.values():
        table.schema = schema_name
    Base.metadata.create_all(bind=engine)

    yield engine, schema_name

    Base.metadata.drop_all(bind=engine)
    for table in Base.metadata.tables.values():
        table.schema = None
    with engine.connect() as conn:
        conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
        conn.commit()
    engine.dispose()


@pytest.fixture()
def db_session(pg_engine):
    _, _ = pg_engine
    Session = sessionmaker(bind=pg_engine[0])
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture()
def service_sessions(pg_engine, monkeypatch):
    """Route the services' SessionLocal to the isolated test schema."""
    from app.services import analytics_service, dashboard_service

    TestSession = sessionmaker(bind=pg_engine[0])
    monkeypatch.setattr(analytics_service, "SessionLocal", TestSession)
    monkeypatch.setattr(dashboard_service, "SessionLocal", TestSession)


@pytest.fixture()
def seeded(db_session, clean_tables):
    """Standard deterministic fixture dataset (defined in test_analytics)."""
    from test_analytics import seed_analytics_data

    return seed_analytics_data(db_session)


@pytest.fixture()
def clean_tables(pg_engine, db_session):
    """Ensure empty tables before AND after each test so tests stay independent."""
    _, schema_name = pg_engine
    table_list = ", ".join(
        f'"{schema_name}".{name}' for name in Base.metadata.tables
    )
    db_session.rollback()
    db_session.execute(text(f"TRUNCATE {table_list}"))
    db_session.commit()
    yield
    db_session.rollback()
    db_session.execute(text(f"TRUNCATE {table_list}"))
    db_session.commit()
