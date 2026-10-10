from fastapi import APIRouter
from app.api.v1.endpoints import (
    agent,

    analytics,
    auth,
    cache,
    categories,
    customers,
    dashboard,
    forecast,
    health,
    inventory,
    orders,
    products,
    sales,
    stores,
)

api_v1_router = APIRouter()


# 1. Authentication & User Profile
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])

# 2. Executive Dashboard & Real-Time KPIs
api_v1_router.include_router(dashboard.router, prefix="/dashboard", tags=["Dashboard"])

# 3. Store Network & Geographic Performance
api_v1_router.include_router(stores.router, prefix="/stores", tags=["Stores"])

# 4. Product Catalog & Merchandising
api_v1_router.include_router(products.router, prefix="/products", tags=["Products"])

# 5. Merchandise Categories
api_v1_router.include_router(categories.router, prefix="/categories", tags=["Categories"])

# 6. Customer Demographics & Cohort Intelligence
api_v1_router.include_router(customers.router, prefix="/customers", tags=["Customers"])

# 7. Sales Orders & Transaction Receipts
api_v1_router.include_router(orders.router, prefix="/orders", tags=["Orders"])

# 8. Financial Sales & Margin Tracking
api_v1_router.include_router(sales.router, prefix="/sales", tags=["Sales"])

# 9. Inventory Positions & Stock Alerts
api_v1_router.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])

# 10. Machine Learning Analytics (Trends, Demand, Pareto)
api_v1_router.include_router(analytics.router, prefix="/analytics", tags=["Analytics"])

# 11. Predictive Sales Forecasting (Prophet & ML)
api_v1_router.include_router(forecast.router, prefix="/forecast", tags=["Forecasting"])

# 12. Autonomous AI Retail Analyst (LangGraph + Gemini)
api_v1_router.include_router(agent.router, prefix="/agent", tags=["AI Retail Analyst"])

# 13. Redis Caching & Cache Invalidation
api_v1_router.include_router(cache.router, prefix="/cache", tags=["Cache Management"])

# 14. System Health & PostgreSQL/PostGIS Diagnostics
api_v1_router.include_router(health.router, tags=["Health"])


