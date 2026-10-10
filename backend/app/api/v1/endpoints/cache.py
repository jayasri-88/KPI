"""
Cache Management and Monitoring Endpoints
Provides real-time Redis operational statistics, hit/miss inspection,
and manual cache invalidation triggers.
"""

from typing import Any, Dict, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field

from app.api.deps import get_current_active_admin, get_current_user
from app.core.cache import cache_manager
from app.models import User

router = APIRouter()


class CacheInvalidateRequest(BaseModel):
    pattern: str = Field(
        default="all",
        description="Cache pattern to invalidate: 'all', 'kpi', 'store', 'product', 'analytics', 'forecast', or custom glob (e.g. 'kpi:dashboard:*')",
    )


class CacheInvalidateResponse(BaseModel):
    pattern: str
    keys_deleted: int
    message: str


@router.get(
    "/stats",
    summary="Get Redis cache performance statistics",
    description="Returns live connection health, hit ratio %, hits, misses, sets, invalidation count, and Redis server telemetry.",
)
def get_cache_stats(
    current_user: User = Depends(get_current_user),
) -> Dict[str, Any]:
    return cache_manager.get_stats()


@router.post(
    "/invalidate",
    response_model=CacheInvalidateResponse,
    status_code=status.HTTP_200_OK,
    summary="Invalidate Redis cache keys",
    description="Clears cache entries by domain pattern. Requires active admin credentials.",
)
def invalidate_cache(
    request: CacheInvalidateRequest,
    admin_user: User = Depends(get_current_active_admin),
) -> CacheInvalidateResponse:
    pattern = request.pattern.strip().lower()

    if pattern in ["all", "retail:*", "*"]:
        deleted = cache_manager.invalidate_all_analytics()
    elif pattern in ["kpi", "dashboard"]:
        deleted = cache_manager.invalidate_dashboard_kpis()
    elif pattern in ["store", "stores"]:
        deleted = cache_manager.invalidate_store_performance()
    elif pattern in ["product", "products"]:
        deleted = cache_manager.invalidate_product_performance()
    elif pattern in ["analytics", "trends"]:
        deleted = cache_manager.invalidate_sales_trends()
    else:
        deleted = cache_manager.delete_pattern(pattern)

    return CacheInvalidateResponse(
        pattern=pattern,
        keys_deleted=deleted,
        message=f"Successfully invalidated {deleted} cached keys for pattern '{pattern}'.",
    )
