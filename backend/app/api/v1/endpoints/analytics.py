"""
Analytics API Endpoints
Provides sales trends, demand distributions, product Pareto rankings, and store analytics.
"""

import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    DemandAnalyticsResponse,
    ProductPerformanceAnalyticsResponse,
    SalesTrendAnalyticsResponse,
    StorePerformance,
)
from app.core.cache import (
    TTL_DEMAND_ANALYTICS,
    TTL_PRODUCT_PERFORMANCE,
    TTL_SALES_TRENDS,
    TTL_STORE_PERFORMANCE,
    cache_manager,
)
from app.services import analytics_service, store_service

router = APIRouter()


@router.get(
    "/sales-trend",
    response_model=SalesTrendAnalyticsResponse,
    summary="Get sales trend analytics",
    description="Returns moving averages (7-day MA, 30-day MA), day-of-week seasonality, volatility, and peak days with Redis caching.",
)
def get_sales_trend(
    store_id: Optional[uuid.UUID] = Query(None, description="Optional store filter"),
    days: int = Query(90, ge=14, le=365, description="Number of historical days to return in trend"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key(
        "analytics:sales_trend",
        days=days,
        store_id=str(store_id) if store_id else None,
    )
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = analytics_service.get_sales_trend_analytics(
        db=db,
        store_id=str(store_id) if store_id else None,
        days=days,
    )
    cache_manager.set(cache_key, data, ttl=TTL_SALES_TRENDS)
    return data


@router.get(
    "/demand",
    response_model=DemandAnalyticsResponse,
    summary="Get cross-category demand analytics",
    description="Returns category-level sales volumes, unit velocity, average selling prices, and revenue share with Redis caching.",
)
def get_demand_analytics(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key("analytics:demand")
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = analytics_service.get_demand_analytics(db=db)
    cache_manager.set(cache_key, data, ttl=TTL_DEMAND_ANALYTICS)
    return data


@router.get(
    "/product-performance",
    response_model=ProductPerformanceAnalyticsResponse,
    summary="Get product performance and Pareto 80/20 analysis",
    description="Evaluates SKU revenues, gross profit margins, and categorizes products into Pareto Class A, B, and C with Redis caching.",
)
def get_product_performance(
    limit: int = Query(50, ge=5, le=200, description="Number of top SKUs to analyze"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key(
        "analytics:product_perf",
        limit=limit,
    )
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = analytics_service.get_product_performance_analytics(db=db, limit=limit)
    cache_manager.set(cache_key, data, ttl=TTL_PRODUCT_PERFORMANCE)
    return data


@router.get(
    "/store-performance",
    response_model=List[StorePerformance],
    summary="Get store performance analytics",
    description="Ranks retail locations by revenue, profit margin, and target achievement percentage with Redis caching.",
)
def get_store_performance(
    region: Optional[str] = Query(None, description="Optional macro-region filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key(
        "analytics:store_perf",
        region=region,
    )
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = store_service.get_stores_performance(db=db, region=region)
    cache_manager.set(cache_key, data, ttl=TTL_STORE_PERFORMANCE)
    return data

