import math
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.core.security import escape_like
from app.models import Customer
from app.schemas import CustomerCreate, CustomerResponse, CustomerUpdate, PaginatedResponse


def get_customers(
    db: Session,
    page: int = 1,
    size: int = 20,
    segment: Optional[str] = None,
    city: Optional[str] = None,
    min_spend: Optional[Decimal] = None,
    max_spend: Optional[Decimal] = None,
    search: Optional[str] = None,
    sort_by: str = "total_spend",
    sort_desc: bool = True,
) -> PaginatedResponse[CustomerResponse]:
    query = db.query(Customer)

    if segment:
        query = query.filter(func.lower(Customer.segment) == segment.strip().lower())
    if city:
        query = query.filter(func.lower(Customer.city) == city.strip().lower())
    if min_spend is not None:
        query = query.filter(Customer.total_spend >= min_spend)
    if max_spend is not None:
        query = query.filter(Customer.total_spend <= max_spend)
    if search:
        s = f"%{escape_like(search.strip().lower())}%"
        query = query.filter(
            or_(
                func.lower(Customer.first_name).like(s),
                func.lower(Customer.last_name).like(s),
                func.lower(Customer.email).like(s),
                func.lower(Customer.city).like(s),
            )
        )

    # Sorting
    sort_column = getattr(Customer, sort_by, Customer.total_spend)
    if sort_desc:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    customers = query.offset(offset).limit(size).all()
    items = [CustomerResponse.model_validate(c) for c in customers]

    return PaginatedResponse[CustomerResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_customer_by_id(db: Session, customer_id: uuid.UUID) -> Optional[Customer]:
    return db.query(Customer).filter(Customer.id == customer_id).first()


def get_customer_by_email(db: Session, email: str) -> Optional[Customer]:
    return db.query(Customer).filter(func.lower(Customer.email) == email.strip().lower()).first()


def create_customer(db: Session, cust_in: CustomerCreate) -> Customer:
    customer = Customer(
        email=cust_in.email.strip().lower(),
        first_name=cust_in.first_name.strip(),
        last_name=cust_in.last_name.strip(),
        phone=cust_in.phone,
        segment=cust_in.segment.strip() if cust_in.segment else "Regular",
        city=cust_in.city.strip() if cust_in.city else None,
        state=cust_in.state.strip() if cust_in.state else None,
        total_spend=Decimal("0.00"),
        total_orders_count=0,
    )
    db.add(customer)
    db.commit()
    db.refresh(customer)
    return customer


def update_customer(
    db: Session,
    customer_id: uuid.UUID,
    cust_in: CustomerUpdate,
) -> Optional[Customer]:
    cust = get_customer_by_id(db, customer_id)
    if not cust:
        return None

    update_data = cust_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "email" and value:
            value = value.strip().lower()
        setattr(cust, field, value)

    db.commit()
    db.refresh(cust)
    return cust


def delete_customer(db: Session, customer_id: uuid.UUID) -> bool:
    cust = get_customer_by_id(db, customer_id)
    if not cust:
        return False
    db.delete(cust)
    db.commit()
    return True


def get_customer_overview(db: Session):
    """Computes customer cohort metrics: total, active, repeat rate, and average revenues."""
    from types import SimpleNamespace
    total_customers = db.query(func.count(Customer.id)).scalar() or 0
    repeat_customers = db.query(func.count(Customer.id)).filter(Customer.total_orders_count > 1).scalar() or 0
    active_customers = db.query(func.count(Customer.id)).filter(Customer.total_orders_count > 0).scalar() or 0
    total_spend_sum = db.query(func.coalesce(func.sum(Customer.total_spend), Decimal("0.00"))).scalar() or Decimal("0.00")
    total_orders_sum = db.query(func.coalesce(func.sum(Customer.total_orders_count), 0)).scalar() or 0

    repeat_rate = (repeat_customers / total_customers * 100.0) if total_customers > 0 else 0.0
    avg_orders = (total_orders_sum / total_customers) if total_customers > 0 else 0.0
    avg_rev = float(total_spend_sum / total_customers) if total_customers > 0 else 0.0

    return SimpleNamespace(
        total_customers=total_customers,
        active_customers=active_customers,
        repeat_customers=repeat_customers,
        repeat_customer_rate_pct=round(repeat_rate, 2),
        average_orders_per_customer=round(avg_orders, 2),
        average_revenue_per_customer=round(avg_rev, 2),
    )


def get_customer_segments(db: Session):
    """Computes distribution, customer count, revenue, and AOV by customer segment."""
    from types import SimpleNamespace
    total_customers = db.query(func.count(Customer.id)).scalar() or 1
    rows = (
        db.query(
            Customer.segment,
            func.count(Customer.id).label("count"),
            func.coalesce(func.sum(Customer.total_spend), Decimal("0.00")).label("revenue"),
            func.coalesce(func.sum(Customer.total_orders_count), 0).label("orders"),
        )
        .group_by(Customer.segment)
        .all()
    )

    results = []
    for r in rows:
        seg_name = r.segment or "Regular"
        cnt = r.count
        rev = float(r.revenue)
        ords = r.orders
        share = round((cnt / total_customers) * 100.0, 2)
        aov = round(rev / ords, 2) if ords > 0 else 0.0
        results.append(
            SimpleNamespace(
                segment=seg_name,
                customer_count=cnt,
                share_pct=share,
                total_revenue=rev,
                avg_order_value=aov,
            )
        )
    return results
