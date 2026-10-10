import uuid
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import (
    PaginatedResponse,
    RegionalPerformanceItem,
    StoreCreate,
    StorePerformance,
    StoreResponse,
    StoreSpatialFeature,
    StoreUpdate,
)
from app.core.cache import TTL_STORE_PERFORMANCE, cache_manager
from app.services import store_service

router = APIRouter()



@router.get(
    "",
    response_model=PaginatedResponse[StoreResponse],
    summary="List retail stores",
    description="Returns paginated list of physical stores with geographic filtering, search, and status checks.",
)
def list_stores(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    region: Optional[str] = Query(None, description="Region: North, South, West, East"),
    city: Optional[str] = Query(None, description="City name"),
    store_type: Optional[str] = Query(None, description="Store type: Flagship, Mall Outlet, Express, Hypermarket"),
    is_active: Optional[bool] = Query(None, description="Filter active/inactive stores"),
    search: Optional[str] = Query(None, description="Search store name, code, or city"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return store_service.get_stores(
        db=db,
        page=page,
        size=size,
        region=region,
        city=city,
        store_type=store_type,
        is_active=is_active,
        search=search,
    )


@router.get(
    "/performance",
    response_model=List[StorePerformance],
    summary="Get store performance rankings",
    description="Returns financial KPIs (revenue, profit, margin %, target achievement %) across retail stores with Redis caching.",
)
def get_store_performance(
    region: Optional[str] = Query(None, description="Filter by geographic region"),
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cache_key = cache_manager.build_key(
        "analytics:store_perf",
        region=region,
        start_date=start_date,
        end_date=end_date,
    )
    cached_data = cache_manager.get(cache_key)
    if cached_data is not None:
        return cached_data

    data = store_service.get_stores_performance(
        db=db,
        region=region,
        start_date=start_date,
        end_date=end_date,
    )
    cache_manager.set(cache_key, data, ttl=TTL_STORE_PERFORMANCE)
    return data



@router.get(
    "/spatial",
    response_model=List[StoreSpatialFeature],
    summary="Get stores with PostGIS spatial metrics",
    description="Returns retail stores enriched with geographic coordinates, PostGIS distance calculations, radius filtering, and real-time sales KPIs.",
)
def get_stores_spatial(
    region: Optional[str] = Query(None, description="Filter by geographic region: North, South, West, East"),
    city: Optional[str] = Query(None, description="Filter by city name"),
    store_type: Optional[str] = Query(None, description="Filter by store type"),
    lat: Optional[float] = Query(None, ge=-90.0, le=90.0, description="Center origin latitude for spatial distance / radius search"),
    lng: Optional[float] = Query(None, ge=-180.0, le=180.0, description="Center origin longitude for spatial distance / radius search"),
    radius_km: Optional[float] = Query(None, gt=0, le=5000, description="Search radius in kilometers from center origin (requires lat/lng)"),
    start_date: Optional[datetime] = Query(None, description="Start date filter for sales calculation"),
    end_date: Optional[datetime] = Query(None, description="End date filter for sales calculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return store_service.get_stores_geographic(
        db=db,
        region=region,
        city=city,
        store_type=store_type,
        lat=lat,
        lng=lng,
        radius_km=radius_km,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/geographic/regions",
    response_model=List[RegionalPerformanceItem],
    summary="Get regional sales performance aggregations",
    description="Calculates geographic and financial aggregations grouped by macro-region, including spatial centroids, regional revenue, profit, and top performing stores.",
)
def get_regional_performance(
    start_date: Optional[datetime] = Query(None, description="Start date filter for sales calculation"),
    end_date: Optional[datetime] = Query(None, description="End date filter for sales calculation"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return store_service.get_regional_sales_aggregation(
        db=db,
        start_date=start_date,
        end_date=end_date,
    )


@router.get(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Get store by ID",
    description="Retrieves single store profile with geographic coordinates.",
)
def get_store(
    store_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    store = store_service.get_store_by_id(db=db, store_id=store_id)
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store '{store_id}' not found.")
    return StoreResponse.model_validate(store)


@router.post(
    "",
    response_model=StoreResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create retail store",
    description="Creates a new store and initializes PostGIS spatial coordinates. Admin only.",
)
def create_store(
    store_in: StoreCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    created = store_service.create_store(db=db, store_in=store_in)
    cache_manager.invalidate_store_performance()
    cache_manager.invalidate_dashboard_kpis()
    return StoreResponse.model_validate(created)


@router.put(
    "/{store_id}",
    response_model=StoreResponse,
    summary="Update store",
    description="Updates store details and coordinates. Admin only.",
)
def update_store(
    store_id: uuid.UUID,
    store_in: StoreUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    store = store_service.update_store(db=db, store_id=store_id, store_in=store_in)
    if not store:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store '{store_id}' not found.")
    cache_manager.invalidate_store_performance()
    cache_manager.invalidate_dashboard_kpis()
    return StoreResponse.model_validate(store)


@router.delete(
    "/{store_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete store",
    description="Deletes a retail store. Admin only.",
)
def delete_store(
    store_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    deleted = store_service.delete_store(db=db, store_id=store_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Store '{store_id}' not found.")
    cache_manager.invalidate_store_performance()
    cache_manager.invalidate_dashboard_kpis()
    return None

