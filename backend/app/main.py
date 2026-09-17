from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.database import init_db, get_db
from app.api.dashboard import router as dashboard_router
from app.api.analytics import router as analytics_router
from app.api.auth import router as auth_router
from app.api.stores import router as stores_router
from app.api.products import router as products_router
from app.api.customers import router as customers_router
from app.api.orders import router as orders_router


app = FastAPI(
    title=settings.app_name,
    description="Retail KPI Intelligence Platform - AI-powered analytics",
    version="1.0.0",
)


app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()


app.include_router(dashboard_router, prefix="/api/dashboard", tags=["Dashboard"])
app.include_router(analytics_router, prefix="/api/analytics", tags=["Analytics"])
app.include_router(auth_router, prefix="/api/auth", tags=["Authentication"])
app.include_router(stores_router, prefix="/api/stores", tags=["Stores"])
app.include_router(products_router, prefix="/api/products", tags=["Products"])
app.include_router(customers_router, prefix="/api/customers", tags=["Customers"])
app.include_router(orders_router, prefix="/api/orders", tags=["Orders"])


@app.get("/")
def root():
    return {
        "message": "Retail KPI Intelligence Platform API is running",
        "version": "1.0.0",
        "status": "ok",
    }


@app.get("/health")
def health():
    db = next(get_db())
    try:
        # Test basic connection
        db.execute("SELECT 1")
        return {
            "application": "healthy",
            "database": "connected",
            "environment": settings.environment,
        }
    except Exception as e:
        return {
            "application": "unhealthy",
            "database": "disconnected",
            "error": str(e),
        }