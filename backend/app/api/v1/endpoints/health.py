import logging
import time
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core.cache import cache_manager
from app.core.config import settings
from app.database import get_db, check_db_connection

logger = logging.getLogger("retail_kpi.health")
router = APIRouter()


@router.get("/health", tags=["Health"])
def get_health_status():
    """
    System health check endpoint verifying API service, PostgreSQL, PostGIS,
    and Redis caching availability with round-trip response metrics.
    """
    t0_db = time.time()
    db_status = check_db_connection()
    db_latency_ms = round((time.time() - t0_db) * 1000, 2)
    is_healthy = db_status["status"] == "connected"

    # Cache diagnostics
    cache_status = "offline"
    cache_latency_ms = None
    if cache_manager.is_available and cache_manager._client:
        try:
            t0_cache = time.time()
            cache_manager._client.ping()
            cache_latency_ms = round((time.time() - t0_cache) * 1000, 2)
            cache_status = "online"
        except Exception:
            cache_status = "error"

    return {
        "status": "healthy" if is_healthy else "degraded",
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "database": {
            "status": db_status["status"],
            "engine": "PostgreSQL",
            "latency_ms": db_latency_ms,
            "version": db_status.get("postgresql"),
            "postgis_version": db_status.get("postgis"),
            "details": db_status.get("details"),
        },
        "cache": {
            "status": cache_status,
            "provider": "Redis",
            "latency_ms": cache_latency_ms,
            "stats": cache_manager.stats,
        },
        "services": {
            "api": "online",
            "database": db_status["status"],
            "postgis": "available" if db_status.get("postgis") else "unavailable",
            "cache": cache_status,
        },
    }


@router.get("/db-check", tags=["Database"])
def verify_database_connection(db: Session = Depends(get_db)):
    """
    Verifies database session management using FastAPI's Depends(get_db) dependency.
    Executes live SQL queries on PostgreSQL and verifies PostGIS extension functions.
    """
    try:
        # Test basic connection and current schema/db
        db_name = db.execute(text("SELECT current_database();")).scalar()
        db_user = db.execute(text("SELECT current_user;")).scalar()
        pg_version = db.execute(text("SELECT version();")).scalar()

        # Test PostGIS spatial capabilities
        postgis_version = db.execute(text("SELECT PostGIS_Version();")).scalar()
        spatial_test = db.execute(
            text("SELECT ST_AsText(ST_MakePoint(77.5946, 12.9716, 4326));")
        ).scalar()

        return {
            "success": True,
            "message": "Database and PostGIS verified successfully via FastAPI dependency injection.",
            "database_name": db_name,
            "connected_user": db_user,
            "postgresql_version": pg_version,
            "postgis_version": postgis_version,
            "spatial_test_geometry": spatial_test,
        }
    except Exception as e:
        logger.error("Database verification failed: %s", e)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Database verification query failed: {str(e)}",
        )
