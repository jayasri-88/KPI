import math
import uuid
from datetime import datetime, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.models import Customer, Order, OrderItem, Product, Sale, Store
from app.schemas import (
    OrderDetailResponse,
    OrderItemCreate,
    OrderItemResponse,
    OrderCreate,
    OrderResponse,
    PaginatedResponse,
)


def _round_dec(val: float | Decimal) -> Decimal:
    if not isinstance(val, Decimal):
        val = Decimal(str(val or 0.0))
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def get_orders(
    db: Session,
    page: int = 1,
    size: int = 20,
    store_id: Optional[uuid.UUID] = None,
    customer_id: Optional[uuid.UUID] = None,
    status: Optional[str] = None,
    channel: Optional[str] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    min_amount: Optional[Decimal] = None,
    max_amount: Optional[Decimal] = None,
    sort_desc: bool = True,
) -> PaginatedResponse[OrderResponse]:
    query = (
        db.query(Order)
        .options(
            joinedload(Order.store),
            joinedload(Order.customer),
        )
    )

    if store_id:
        query = query.filter(Order.store_id == store_id)
    if customer_id:
        query = query.filter(Order.customer_id == customer_id)
    if status:
        query = query.filter(func.lower(Order.status) == status.strip().lower())
    if channel:
        query = query.filter(func.lower(Order.channel) == channel.strip().lower())
    if start_date:
        query = query.filter(Order.order_date >= start_date)
    if end_date:
        query = query.filter(Order.order_date <= end_date)
    if min_amount is not None:
        query = query.filter(Order.total_amount >= min_amount)
    if max_amount is not None:
        query = query.filter(Order.total_amount <= max_amount)

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    if sort_desc:
        query = query.order_by(Order.order_date.desc())
    else:
        query = query.order_by(Order.order_date.asc())

    orders = query.offset(offset).limit(size).all()

    items = []
    for o in orders:
        resp = OrderResponse.model_validate(o)
        resp.store_name = o.store.name if o.store else None
        resp.customer_name = (
            f"{o.customer.first_name} {o.customer.last_name}" if o.customer else None
        )
        items.append(resp)

    return PaginatedResponse[OrderResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_order_by_id(db: Session, order_id: uuid.UUID) -> Optional[OrderDetailResponse]:
    order = (
        db.query(Order)
        .options(
            joinedload(Order.store),
            joinedload(Order.customer),
            joinedload(Order.order_items).joinedload(OrderItem.product),
        )
        .filter(Order.id == order_id)
        .first()
    )
    if not order:
        return None

    resp = OrderDetailResponse.model_validate(order)
    resp.store_name = order.store.name if order.store else None
    resp.customer_name = (
        f"{order.customer.first_name} {order.customer.last_name}"
        if order.customer
        else None
    )

    items_list: List[OrderItemResponse] = []
    for item in order.order_items:
        i_resp = OrderItemResponse.model_validate(item)
        i_resp.product_name = item.product.product_name if item.product else None
        i_resp.sku_code = item.product.sku_code if item.product else None
        items_list.append(i_resp)

    resp.order_items = items_list
    return resp


def create_order(db: Session, order_in: OrderCreate) -> OrderDetailResponse:
    """
    Atomic transaction:
    1. Validates store and customer
    2. Computes line totals and order totals with 18% GST tax
    3. Creates Order, OrderItem, and Sale records
    4. Updates Customer lifetime spend and order count
    """
    store = db.query(Store).filter(Store.id == order_in.store_id).first()
    if not store:
        raise ValueError(f"Store with ID '{order_in.store_id}' not found.")

    customer = None
    if order_in.customer_id:
        customer = db.query(Customer).filter(Customer.id == order_in.customer_id).first()
        if not customer:
            raise ValueError(f"Customer with ID '{order_in.customer_id}' not found.")

    order_date = order_in.order_date or datetime.now(timezone.utc)
    order_number = f"ORD-{order_date.strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"

    # Calculate item totals
    subtotal = Decimal("0.00")
    total_discount = Decimal("0.00")
    total_qty = 0

    order_id = uuid.uuid4()
    order_items_objs: List[OrderItem] = []
    sales_objs: List[Sale] = []

    for item in order_in.items:
        product = db.query(Product).filter(Product.id == item.product_id).first()
        if not product:
            raise ValueError(f"Product with ID '{item.product_id}' not found.")

        line_gross = _round_dec(item.unit_price * Decimal(item.quantity))
        line_disc = _round_dec(item.discount_amount)
        line_net = _round_dec(line_gross - line_disc)
        cogs = _round_dec(item.unit_cost * Decimal(item.quantity))
        profit = _round_dec(line_net - cogs)
        margin = _round_dec((profit / line_net) * Decimal("100.00")) if line_net > 0 else Decimal("0.00")

        subtotal += line_gross
        total_discount += line_disc
        total_qty += item.quantity

        order_items_objs.append(
            OrderItem(
                id=uuid.uuid4(),
                order_id=order_id,
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=item.unit_price,
                unit_cost=item.unit_cost,
                discount_amount=line_disc,
                total_price=line_net,
            )
        )

        sales_objs.append(
            Sale(
                id=uuid.uuid4(),
                order_id=order_id,
                store_id=order_in.store_id,
                product_id=item.product_id,
                sale_date=order_date,
                channel=order_in.channel,
                quantity=item.quantity,
                unit_price=item.unit_price,
                cost_price=item.unit_cost,
                revenue=line_net,
                cogs=cogs,
                gross_profit=profit,
                margin_pct=margin,
            )
        )

    # 18% GST tax on taxable base
    taxable_base = _round_dec(subtotal - total_discount)
    tax_amount = _round_dec(taxable_base * Decimal("0.18"))
    total_amount = _round_dec(taxable_base + tax_amount)

    new_order = Order(
        id=order_id,
        order_number=order_number,
        store_id=order_in.store_id,
        customer_id=order_in.customer_id,
        order_date=order_date,
        status="completed",
        channel=order_in.channel,
        payment_method=order_in.payment_method,
        subtotal=subtotal,
        discount_amount=total_discount,
        tax_amount=tax_amount,
        total_amount=total_amount,
        total_items=total_qty,
    )

    db.add(new_order)
    for oi in order_items_objs:
        db.add(oi)
    for s in sales_objs:
        db.add(s)

    # Update Customer Aggregates
    if customer:
        customer.total_spend += total_amount
        customer.total_orders_count += 1
        customer.last_order_date = order_date

    db.commit()
    db.refresh(new_order)

    # Invalidate dashboard, store performance, product performance, and sales trend caches
    try:
        from app.core.cache import cache_manager
        cache_manager.invalidate_all_analytics()
    except Exception:
        pass

    return get_order_by_id(db, new_order.id)

