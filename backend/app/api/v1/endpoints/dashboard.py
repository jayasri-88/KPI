from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    DashboardOverviewResponse,
    SalesTrendResponse,
    TopProductItem,
    TopStoreItem,
)
from app.core.cache import TTL_DASHBOARD_KPIS, TTL_SALES_TRENDS, cache_manager
from app.services import dashboard_service

router = APIRouter()


@router.get(
    "/overview",
    response_model=DashboardOverviewResponse,
    summary="Get executive KPI dashboard overview",
    description="Calculates real-time financial KPIs (revenue, profit, orders, customers, AOV, growth, top products & stores) from PostgreSQL with Redis caching.",
)
def get_dashboard_overview(
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key(
        "kpi:dashboard",
        start_date=start_date,
        end_date=end_date,
    )
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = dashboard_service.get_dashboard_kpis(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )
    cache_manager.set(cache_key, data, ttl=TTL_DASHBOARD_KPIS)
    return data


@router.get(
    "/sales-trend",
    response_model=SalesTrendResponse,
    summary="Get historical sales trend data",
    description="Groups sales and gross profit by daily, weekly, or monthly intervals for timeline charts with Redis caching.",
)
def get_sales_trend(
    interval: str = Query("monthly", pattern="^(daily|weekly|monthly)$", description="Aggregation bucket interval"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key(
        "kpi:sales_trend",
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = dashboard_service.get_sales_trend(
        db=db,
        interval=interval,
        start_date=start_date,
        end_date=end_date,
    )
    cache_manager.set(cache_key, data, ttl=TTL_SALES_TRENDS)
    return data



@router.get(
    "/top-products",
    response_model=List[TopProductItem],
    summary="Get top performing products",
    description="Returns top ranked products by consolidated revenue and units sold.",
)
def get_top_products(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(5, ge=1, le=20, description="Max products to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    overview = dashboard_service.get_dashboard_kpis(db=db, start_date=start_date, end_date=end_date)
    return overview.top_products[:limit]


@router.get(
    "/top-stores",
    response_model=List[TopStoreItem],
    summary="Get top performing retail stores",
    description="Returns top ranked stores by revenue and target achievement.",
)
def get_top_stores(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    limit: int = Query(5, ge=1, le=20, description="Max stores to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    overview = dashboard_service.get_dashboard_kpis(db=db, start_date=start_date, end_date=end_date)
    return overview.top_stores[:limit]
