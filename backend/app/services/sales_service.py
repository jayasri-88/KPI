import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import Optional
from sqlalchemy import func, desc
from sqlalchemy.orm import Session

from app.models import Product, Sale, Store
from app.schemas import PaginatedResponse, SaleResponse, SalesSummary


def _round_dec(val: float | Decimal) -> Decimal:
    if not isinstance(val, Decimal):
        val = Decimal(str(val or 0.0))
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_sales(
    db: Session,
    page: int = 1,
    size: int = 20,
    store_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
    channel: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_revenue: Optional[Decimal] = None,
    max_revenue: Optional[Decimal] = None,
    sort_by: str = "sale_date",
    sort_desc: bool = True,
) -> PaginatedResponse[SaleResponse]:
    query = (
        db.query(Sale)
        .join(Store, Sale.store_id == Store.id)
        .join(Product, Sale.product_id == Product.id)
    )

    if store_id:
        query = query.filter(Sale.store_id == store_id)
    if product_id:
        query = query.filter(Sale.product_id == product_id)
    if channel:
        query = query.filter(func.lower(Sale.channel) == channel.strip().lower())
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    if min_revenue is not None:
        query = query.filter(Sale.revenue >= min_revenue)
    if max_revenue is not None:
        query = query.filter(Sale.revenue <= max_revenue)

    # Sorting
    sort_column = getattr(Sale, sort_by, Sale.sale_date)
    if sort_desc:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    sales = query.offset(offset).limit(size).all()

    items = []
    for s in sales:
        resp = SaleResponse.model_validate(s)
        resp.store_name = s.store.name if s.store else None
        resp.product_name = s.product.product_name if s.product else None
        resp.sku_code = s.product.sku_code if s.product else None
        items.append(resp)

    return PaginatedResponse[SaleResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_sales_summary(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    store_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
) -> SalesSummary:
    query = db.query(Sale)
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)
    if store_id:
        query = query.filter(Sale.store_id == store_id)
    if product_id:
        query = query.filter(Sale.product_id == product_id)

    agg = query.with_entities(
        func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("revenue"),
        func.coalesce(func.sum(Sale.cogs), Decimal("0.00")).label("cogs"),
        func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("profit"),
        func.count(func.distinct(Sale.order_id)).label("orders_count"),
        func.coalesce(func.sum(Sale.quantity), 0).label("quantity"),
    ).first()

    rev = _round_dec(agg.revenue if agg else Decimal("0.00"))
    cogs = _round_dec(agg.cogs if agg else Decimal("0.00"))
    profit = _round_dec(agg.profit if agg else Decimal("0.00"))
    margin = _round_dec((profit / rev) * Decimal("100.00")) if rev > Decimal("0.00") else Decimal("0.00")
    orders = int(agg.orders_count or 0) if agg else 0
    qty = int(agg.quantity or 0) if agg else 0
    aov = _round_dec(rev / Decimal(orders)) if orders > 0 else Decimal("0.00")

    return SalesSummary(
        date=end_date or datetime.now(timezone.utc),
        total_revenue=rev,
        total_cogs=cogs,
        total_profit=profit,
        margin_pct=margin,
        total_orders=orders,
        total_quantity=qty,
        average_order_value=aov,
    )


def get_sale_by_id(db: Session, sale_id: uuid.UUID) -> Optional[Sale]:
    return db.query(Sale).filter(Sale.id == sale_id).first()
