import math
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional, Tuple
from geoalchemy2 import Geography
from geoalchemy2.elements import WKTElement
from sqlalchemy import cast, desc, func, or_
from sqlalchemy.orm import Session

from app.core.security import escape_like
from app.models import Order, Sale, Store
from app.schemas import (
    PaginatedResponse,
    RegionalPerformanceItem,
    StoreCreate,
    StorePerformance,
    StoreResponse,
    StoreSpatialFeature,
    StoreUpdate,
)


def _round_dec(val: float | Decimal, places: int = 2) -> Decimal:
    if not isinstance(val, Decimal):
        val = Decimal(str(val or 0.0))
    return val.quantize(Decimal(f"0.{'0' * places}"), rounding=ROUND_HALF_UP)


def get_stores(
    db: Session,
    page: int = 1,
    size: int = 20,
    region: Optional[str] = None,
    city: Optional[str] = None,
    store_type: Optional[str] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
) -> PaginatedResponse[StoreResponse]:
    query = db.query(Store)

    if region:
        query = query.filter(func.lower(Store.region) == region.strip().lower())
    if city:
        query = query.filter(func.lower(Store.city) == city.strip().lower())
    if store_type:
        query = query.filter(func.lower(Store.store_type) == store_type.strip().lower())
    if is_active is not None:
        query = query.filter(Store.is_active == is_active)
    if search:
        s = f"%{escape_like(search.strip().lower())}%"
        query = query.filter(
            or_(
                func.lower(Store.name).like(s),
                func.lower(Store.store_code).like(s),
                func.lower(Store.city).like(s),
            )
        )

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size
    stores = query.order_by(Store.name.asc()).offset(offset).limit(size).all()

    items = [StoreResponse.model_validate(s) for s in stores]
    return PaginatedResponse[StoreResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_store_by_id(db: Session, store_id: uuid.UUID) -> Optional[Store]:
    return db.query(Store).filter(Store.id == store_id).first()


def create_store(db: Session, store_in: StoreCreate) -> Store:
    location_wkt = WKTElement(f"POINT({store_in.longitude} {store_in.latitude})", srid=4326)
    store = Store(
        store_code=store_in.store_code.strip().upper(),
        name=store_in.name.strip(),
        store_type=store_in.store_type.strip(),
        address=store_in.address,
        city=store_in.city.strip(),
        state=store_in.state.strip(),
        region=store_in.region.strip(),
        postal_code=store_in.postal_code,
        latitude=store_in.latitude,
        longitude=store_in.longitude,
        location=location_wkt,
        store_size_sqft=store_in.store_size_sqft,
        target_monthly_sales=store_in.target_monthly_sales,
        is_active=store_in.is_active,
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


def update_store(db: Session, store_id: uuid.UUID, store_in: StoreUpdate) -> Optional[Store]:
    store = get_store_by_id(db, store_id)
    if not store:
        return None

    update_data = store_in.model_dump(exclude_unset=True)
    if "latitude" in update_data or "longitude" in update_data:
        new_lat = update_data.get("latitude", store.latitude)
        new_lng = update_data.get("longitude", store.longitude)
        store.location = WKTElement(f"POINT({new_lng} {new_lat})", srid=4326)

    for field, value in update_data.items():
        setattr(store, field, value)

    db.commit()
    db.refresh(store)
    return store


def delete_store(db: Session, store_id: uuid.UUID) -> bool:
    store = get_store_by_id(db, store_id)
    if not store:
        return False
    db.delete(store)
    db.commit()
    return True


def get_stores_performance(
    db: Session,
    region: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[StorePerformance]:
    """
    Ranks and calculates financial KPIs for all physical retail locations.
    """
    sales_subquery = db.query(
        Sale.store_id,
        func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("revenue"),
        func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("profit"),
        func.count(func.distinct(Sale.order_id)).label("orders_count"),
    )
    if start_date:
        sales_subquery = sales_subquery.filter(Sale.sale_date >= start_date)
    if end_date:
        sales_subquery = sales_subquery.filter(Sale.sale_date <= end_date)
    sales_subquery = sales_subquery.group_by(Sale.store_id).subquery()

    query = (
        db.query(
            Store,
            func.coalesce(sales_subquery.c.revenue, Decimal("0.00")).label("revenue"),
            func.coalesce(sales_subquery.c.profit, Decimal("0.00")).label("profit"),
            func.coalesce(sales_subquery.c.orders_count, 0).label("orders_count"),
        )
        .outerjoin(sales_subquery, Store.id == sales_subquery.c.store_id)
    )

    if region:
        query = query.filter(func.lower(Store.region) == region.strip().lower())

    rows = query.order_by(desc("revenue")).all()

    results: List[StorePerformance] = []
    for store, rev, prof, orders in rows:
        rev_dec = _round_dec(rev)
        prof_dec = _round_dec(prof)
        orders_int = int(orders)
        aov = _round_dec(rev_dec / Decimal(orders_int)) if orders_int > 0 else Decimal("0.00")
        margin = _round_dec((prof_dec / rev_dec) * Decimal("100.00")) if rev_dec > Decimal("0.00") else Decimal("0.00")
        target = _round_dec(store.target_monthly_sales)
        achieve = _round_dec((rev_dec / target) * Decimal("100.00")) if target > Decimal("0.00") else Decimal("0.00")

        results.append(
            StorePerformance(
                store_id=store.id,
                store_code=store.store_code,
                name=store.name,
                city=store.city,
                region=store.region,
                store_type=store.store_type,
                latitude=store.latitude,
                longitude=store.longitude,
                total_revenue=rev_dec,
                total_orders=orders_int,
                average_order_value=aov,
                total_profit=prof_dec,
                profit_margin_pct=margin,
                target_monthly_sales=target,
                target_achievement_pct=achieve,
            )
        )

    return results


def get_stores_geographic(
    db: Session,
    region: Optional[str] = None,
    city: Optional[str] = None,
    store_type: Optional[str] = None,
    lat: Optional[float] = None,
    lng: Optional[float] = None,
    radius_km: Optional[float] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[StoreSpatialFeature]:
    """
    Retrieves retail stores enriched with PostGIS distance calculations,
    spatial proximity filtering, and real-time financial KPIs.
    """
    sales_subquery = db.query(
        Sale.store_id,
        func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("revenue"),
        func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("profit"),
        func.count(func.distinct(Sale.order_id)).label("orders_count"),
    )
    if start_date:
        sales_subquery = sales_subquery.filter(Sale.sale_date >= start_date)
    if end_date:
        sales_subquery = sales_subquery.filter(Sale.sale_date <= end_date)
    sales_subquery = sales_subquery.group_by(Sale.store_id).subquery()

    has_origin = lat is not None and lng is not None
    dist_col = None

    if has_origin:
        origin_geom = func.ST_SetSRID(func.ST_MakePoint(lng, lat), 4326)
        dist_expr = (
            func.ST_Distance(
                cast(Store.location, Geography),
                cast(origin_geom, Geography),
            )
            / 1000.0
        )
        dist_col = dist_expr.label("distance_km")

    columns = [
        Store,
        func.coalesce(sales_subquery.c.revenue, Decimal("0.00")).label("revenue"),
        func.coalesce(sales_subquery.c.profit, Decimal("0.00")).label("profit"),
        func.coalesce(sales_subquery.c.orders_count, 0).label("orders_count"),
    ]
    if dist_col is not None:
        columns.append(dist_col)

    query = db.query(*columns).outerjoin(sales_subquery, Store.id == sales_subquery.c.store_id)

    if region:
        query = query.filter(func.lower(Store.region) == region.strip().lower())
    if city:
        query = query.filter(func.lower(Store.city) == city.strip().lower())
    if store_type:
        query = query.filter(func.lower(Store.store_type) == store_type.strip().lower())

    if has_origin and radius_km is not None and radius_km > 0:
        query = query.filter(
            func.ST_DWithin(
                cast(Store.location, Geography),
                cast(origin_geom, Geography),
                radius_km * 1000.0,
            )
        )

    if has_origin:
        query = query.order_by(dist_col.asc())
    else:
        query = query.order_by(desc("revenue"))

    rows = query.all()
    results: List[StoreSpatialFeature] = []

    for row in rows:
        store = row[0]
        rev = _round_dec(row[1])
        prof = _round_dec(row[2])
        orders = int(row[3])
        dist = round(float(row[4]), 2) if has_origin and len(row) > 4 and row[4] is not None else None

        aov = _round_dec(rev / Decimal(orders)) if orders > 0 else Decimal("0.00")
        margin = _round_dec((prof / rev) * Decimal("100.00")) if rev > Decimal("0.00") else Decimal("0.00")
        target = _round_dec(store.target_monthly_sales)
        achieve = _round_dec((rev / target) * Decimal("100.00")) if target > Decimal("0.00") else Decimal("0.00")
        sales_per_sqft = (
            _round_dec(rev / Decimal(store.store_size_sqft)) if store.store_size_sqft > 0 else Decimal("0.00")
        )

        results.append(
            StoreSpatialFeature(
                store_id=store.id,
                store_code=store.store_code,
                name=store.name,
                store_type=store.store_type,
                address=store.address,
                city=store.city,
                state=store.state,
                region=store.region,
                postal_code=store.postal_code,
                latitude=store.latitude,
                longitude=store.longitude,
                store_size_sqft=store.store_size_sqft,
                target_monthly_sales=target,
                is_active=store.is_active,
                total_revenue=rev,
                total_profit=prof,
                total_orders=orders,
                average_order_value=aov,
                profit_margin_pct=margin,
                target_achievement_pct=achieve,
                sales_per_sqft=sales_per_sqft,
                distance_km=dist,
            )
        )

    return results


def get_regional_sales_aggregation(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[RegionalPerformanceItem]:
    """
    Computes spatial and financial aggregations grouped by geographic region.
    Includes regional revenue, profit, AOV, target achievement, and spatial centroid.
    """
    sales_subquery = db.query(
        Sale.store_id,
        func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("revenue"),
        func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("profit"),
        func.count(func.distinct(Sale.order_id)).label("orders_count"),
    )
    if start_date:
        sales_subquery = sales_subquery.filter(Sale.sale_date >= start_date)
    if end_date:
        sales_subquery = sales_subquery.filter(Sale.sale_date <= end_date)
    sales_subquery = sales_subquery.group_by(Sale.store_id).subquery()

    query = (
        db.query(
            Store.region,
            func.count(Store.id).label("store_count"),
            func.coalesce(func.sum(sales_subquery.c.revenue), Decimal("0.00")).label("total_revenue"),
            func.coalesce(func.sum(sales_subquery.c.profit), Decimal("0.00")).label("total_profit"),
            func.coalesce(func.sum(sales_subquery.c.orders_count), 0).label("total_orders"),
            func.coalesce(func.sum(Store.target_monthly_sales), Decimal("0.00")).label("total_target"),
            func.avg(Store.latitude).label("centroid_lat"),
            func.avg(Store.longitude).label("centroid_lng"),
        )
        .outerjoin(sales_subquery, Store.id == sales_subquery.c.store_id)
        .group_by(Store.region)
        .order_by(desc("total_revenue"))
    )

    rows = query.all()

    # Find top store for each region
    top_store_query = (
        db.query(
            Store.region,
            Store.name,
            func.coalesce(sales_subquery.c.revenue, Decimal("0.00")).label("store_revenue"),
        )
        .outerjoin(sales_subquery, Store.id == sales_subquery.c.store_id)
        .order_by(Store.region, desc("store_revenue"))
        .all()
    )
    top_store_by_region = {}
    for r_name, s_name, _ in top_store_query:
        if r_name not in top_store_by_region:
            top_store_by_region[r_name] = s_name

    results: List[RegionalPerformanceItem] = []
    for row in rows:
        rev = _round_dec(row.total_revenue)
        profit = _round_dec(row.total_profit)
        orders = int(row.total_orders)
        target = _round_dec(row.total_target)
        aov = _round_dec(rev / Decimal(orders)) if orders > 0 else Decimal("0.00")
        margin = _round_dec((profit / rev) * Decimal("100.00")) if rev > Decimal("0.00") else Decimal("0.00")
        achieve = _round_dec((rev / target) * Decimal("100.00")) if target > Decimal("0.00") else Decimal("0.00")

        results.append(
            RegionalPerformanceItem(
                region=row.region,
                store_count=int(row.store_count),
                total_revenue=rev,
                total_profit=profit,
                total_orders=orders,
                average_order_value=aov,
                profit_margin_pct=margin,
                target_achievement_pct=achieve,
                centroid_lat=round(float(row.centroid_lat), 4) if row.centroid_lat is not None else None,
                centroid_lng=round(float(row.centroid_lng), 4) if row.centroid_lng is not None else None,
                top_store_name=top_store_by_region.get(row.region),
            )
        )

    return results
