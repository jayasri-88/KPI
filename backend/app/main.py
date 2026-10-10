import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.core.cache import cache_manager
from app.core.config import settings
from app.database import enable_postgis
from app.api.v1.api import api_v1_router
from app.api.v1.endpoints.health import get_health_status

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("retail_kpi")


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Initializing %s (v%s) in [%s] mode...", settings.app_name, settings.app_version, settings.environment)
    # Ensure PostGIS spatial extension is ready
    enable_postgis()
    logger.info("Phase 2 active. PostgreSQL & PostGIS connected.")

    # Verify Redis Caching
    if cache_manager.is_available:
        logger.info("Phase 10 active. Redis Cache connected at %s.", settings.redis_url)
    else:
        logger.warning("Phase 10 active. Redis Cache offline. Running in graceful PostgreSQL direct fallback mode.")

    logger.info("Routes ready at %s", settings.api_v1_str)
    yield
    logger.info("Shutting down %s...", settings.app_name)



app = FastAPI(
    title=settings.app_name,
    description="Retail KPI Intelligence Platform - PostgreSQL & PostGIS Spatial Analytics Engine",
    version=settings.app_version,
    openapi_url=f"{settings.api_v1_str}/openapi.json",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware - strict trusted origins + Vercel dynamic deployment subdomains
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_origin_regex=r"^https:\/\/.*\.vercel\.app$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global Exception Handlers for structured error responses
@app.exception_handler(StarletteHTTPException)
async def http_exception_handler(request: Request, exc: StarletteHTTPException):
    logger.warning("HTTP %s on %s %s: %s", exc.status_code, request.method, request.url.path, exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": f"HTTP_{exc.status_code}",
                "message": exc.detail if isinstance(exc.detail, str) else "HTTP Exception",
                "details": exc.detail if not isinstance(exc.detail, str) else None,
            },
            "detail": exc.detail if isinstance(exc.detail, str) else str(exc.detail),
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    logger.warning("Validation error on %s %s: %s", request.method, request.url.path, exc.errors())
    formatted_errors = [
        {"loc": list(err.get("loc", [])), "msg": err.get("msg", ""), "type": err.get("type", "")}
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request payload validation failed.",
                "details": formatted_errors,
            },
            "detail": formatted_errors,
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception on %s %s: %s", request.method, request.url.path, exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected server error occurred. Please contact the administrator.",
                "details": str(exc) if settings.debug else None,
            },
            "detail": "An unexpected server error occurred.",
        },
    )


@app.get("/", tags=["Root"])
def root():
    """Root platform metadata endpoint."""
    return {
        "app_name": settings.app_name,
        "version": settings.app_version,
        "environment": settings.environment,
        "status": "online",
        "phase": "Phase 2: PostgreSQL + PostGIS + SQLAlchemy",
        "docs_url": "/docs",
        "health_check": f"{settings.api_v1_str}/health",
        "db_check": f"{settings.api_v1_str}/db-check",
    }


# Health check endpoint aliases for convenience
@app.get("/health", tags=["Health"])
@app.get("/api/health", tags=["Health"])
def health_alias():
    """Convenience alias for /api/v1/health."""
    return get_health_status()


# Mount versioned API routes
app.include_router(api_v1_router, prefix=settings.api_v1_str)