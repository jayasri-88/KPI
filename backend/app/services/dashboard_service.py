from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP
from typing import List, Optional
from sqlalchemy import func, desc, distinct
from sqlalchemy.orm import Session

from app.models import Category, Customer, Order, OrderItem, Product, Sale, Store
from app.schemas import (
    CategoryRevenueItem,
    DashboardOverviewResponse,
    RecentOrderItem,
    SalesTrendPoint,
    SalesTrendResponse,
    TopProductItem,
    TopStoreItem,
)


def _round_dec(val: float | Decimal, places: int = 2) -> Decimal:
    """Helper to ensure currency decimals are rounded cleanly."""
    if not isinstance(val, Decimal):
        val = Decimal(str(val or 0.0))
    return val.quantize(Decimal(f"0.{'0' * places}"), rounding=ROUND_HALF_UP)


def get_dashboard_kpis(
    db: Session,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> DashboardOverviewResponse:
    """
    Computes real-time executive dashboard KPIs from PostgreSQL:
    - Total Revenue, COGS, and Gross Profit
    - Total Orders and Total Customers
    - Average Order Value (AOV) and Gross Margin %
    - Growth rates compared to previous identical duration period
    - Top performing products by revenue
    - Top performing stores by revenue
    - Category sales distribution and share %
    - Recent order stream
    """
    # 1. Base Query Filters for Current Period
    sales_query = db.query(Sale)
    orders_query = db.query(Order)

    if start_date:
        sales_query = sales_query.filter(Sale.sale_date >= start_date)
        orders_query = orders_query.filter(Order.order_date >= start_date)
    if end_date:
        sales_query = sales_query.filter(Sale.sale_date <= end_date)
        orders_query = orders_query.filter(Order.order_date <= end_date)

    # 2. Financial Aggregates
    fin_agg = sales_query.with_entities(
        func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("revenue"),
        func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("profit"),
        func.coalesce(func.sum(Sale.cogs), Decimal("0.00")).label("cogs"),
    ).first()

    total_revenue = _round_dec(fin_agg.revenue if fin_agg else Decimal("0.00"))
    total_profit = _round_dec(fin_agg.profit if fin_agg else Decimal("0.00"))

    # 3. Order & Customer Counts
    total_orders = orders_query.count()

    total_customers_res = orders_query.with_entities(
        func.count(distinct(Order.customer_id))
    ).scalar()
    total_customers = int(total_customers_res or 0)

    # 4. Computed Ratios
    aov = (
        _round_dec(total_revenue / Decimal(total_orders))
        if total_orders > 0
        else Decimal("0.00")
    )
    gross_margin_pct = (
        _round_dec((total_profit / total_revenue) * Decimal("100.00"))
        if total_revenue > Decimal("0.00")
        else Decimal("0.00")
    )

    # 5. Growth Rates (Compare against previous equivalent period)
    # If no date filter is passed, compare the most recent 30 days vs the prior 30 days
    now = datetime.now(timezone.utc)
    if start_date and end_date:
        duration = end_date - start_date
        prev_start = start_date - duration
        prev_end = start_date
    else:
        # Latest 30 days vs prior 30 days
        max_date_res = db.query(func.max(Sale.sale_date)).scalar()
        ref_date = max_date_res or now
        curr_30_start = ref_date - timedelta(days=30)
        prev_start = curr_30_start - timedelta(days=30)
        prev_end = curr_30_start

    prev_agg = (
        db.query(
            func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("revenue"),
            func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("profit"),
            func.count(distinct(Sale.order_id)).label("orders"),
        )
        .filter(Sale.sale_date >= prev_start, Sale.sale_date < prev_end)
        .first()
    )

    prev_revenue = _round_dec(prev_agg.revenue if prev_agg else Decimal("0.00"))
    prev_profit = _round_dec(prev_agg.profit if prev_agg else Decimal("0.00"))
    prev_orders = int(prev_agg.orders or 0) if prev_agg else 0

    def calc_growth(current: Decimal, previous: Decimal) -> Decimal:
        if previous > Decimal("0.00"):
            return _round_dec(((current - previous) / previous) * Decimal("100.00"))
        return Decimal("100.00") if current > Decimal("0.00") else Decimal("0.00")

    rev_growth = calc_growth(total_revenue, prev_revenue)
    prof_growth = calc_growth(total_profit, prev_profit)
    orders_growth = calc_growth(Decimal(total_orders), Decimal(prev_orders))

    # 6. Top 5 Products by Revenue
    top_prod_rows = (
        sales_query.join(Product, Sale.product_id == Product.id)
        .join(Category, Product.category_id == Category.id)
        .with_entities(
            Product.id.label("product_id"),
            Product.sku_code.label("sku_code"),
            Product.product_name.label("product_name"),
            Product.brand.label("brand"),
            Category.name.label("category_name"),
            func.sum(Sale.quantity).label("units_sold"),
            func.sum(Sale.revenue).label("revenue"),
            func.sum(Sale.gross_profit).label("profit"),
        )
        .group_by(Product.id, Product.sku_code, Product.product_name, Product.brand, Category.name)
        .order_by(desc("revenue"))
        .limit(5)
        .all()
    )

    top_products: List[TopProductItem] = []
    for r in top_prod_rows:
        prod_rev = _round_dec(r.revenue)
        prod_prof = _round_dec(r.profit)
        margin = (
            _round_dec((prod_prof / prod_rev) * Decimal("100.00"))
            if prod_rev > 0
            else Decimal("0.00")
        )
        top_products.append(
            TopProductItem(
                product_id=r.product_id,
                sku_code=r.sku_code,
                product_name=r.product_name,
                brand=r.brand,
                category_name=r.category_name,
                units_sold=int(r.units_sold or 0),
                revenue=prod_rev,
                profit=prod_prof,
                margin_pct=margin,
            )
        )

    # 7. Top 5 Stores by Revenue
    top_store_rows = (
        sales_query.join(Store, Sale.store_id == Store.id)
        .with_entities(
            Store.id.label("store_id"),
            Store.store_code.label("store_code"),
            Store.name.label("name"),
            Store.city.label("city"),
            Store.region.label("region"),
            Store.target_monthly_sales.label("target"),
            func.sum(Sale.revenue).label("revenue"),
            func.sum(Sale.gross_profit).label("profit"),
            func.count(distinct(Sale.order_id)).label("orders_count"),
        )
        .group_by(Store.id, Store.store_code, Store.name, Store.city, Store.region, Store.target_monthly_sales)
        .order_by(desc("revenue"))
        .limit(5)
        .all()
    )

    top_stores: List[TopStoreItem] = []
    for s in top_store_rows:
        st_rev = _round_dec(s.revenue)
        st_prof = _round_dec(s.profit)
        st_target = _round_dec(s.target)
        achieve = (
            _round_dec((st_rev / st_target) * Decimal("100.00"))
            if st_target > 0
            else Decimal("0.00")
        )
        top_stores.append(
            TopStoreItem(
                store_id=s.store_id,
                store_code=s.store_code,
                name=s.name,
                city=s.city,
                region=s.region,
                revenue=st_rev,
                profit=st_prof,
                orders_count=int(s.orders_count or 0),
                target_achievement_pct=achieve,
            )
        )

    # 8. Category Revenue Distribution
    cat_rows = (
        sales_query.join(Product, Sale.product_id == Product.id)
        .join(Category, Product.category_id == Category.id)
        .with_entities(
            Category.id.label("category_id"),
            Category.name.label("category_name"),
            func.sum(Sale.revenue).label("revenue"),
            func.sum(Sale.quantity).label("units_sold"),
        )
        .group_by(Category.id, Category.name)
        .order_by(desc("revenue"))
        .all()
    )

    category_dist: List[CategoryRevenueItem] = []
    for c in cat_rows:
        c_rev = _round_dec(c.revenue)
        share = (
            _round_dec((c_rev / total_revenue) * Decimal("100.00"))
            if total_revenue > 0
            else Decimal("0.00")
        )
        category_dist.append(
            CategoryRevenueItem(
                category_id=c.category_id,
                category_name=c.category_name,
                revenue=c_rev,
                units_sold=int(c.units_sold or 0),
                share_pct=share,
            )
        )

    # 9. Recent 5 Orders
    recent_order_rows = (
        orders_query.join(Store, Order.store_id == Store.id)
        .outerjoin(Customer, Order.customer_id == Customer.id)
        .with_entities(
            Order.id.label("order_id"),
            Order.order_number.label("order_number"),
            Store.name.label("store_name"),
            func.concat(Customer.first_name, " ", Customer.last_name).label("customer_name"),
            Order.order_date.label("order_date"),
            Order.total_amount.label("total_amount"),
            Order.status.label("status"),
        )
        .order_by(desc(Order.order_date))
        .limit(5)
        .all()
    )

    recent_orders: List[RecentOrderItem] = [
        RecentOrderItem(
            order_id=o.order_id,
            order_number=o.order_number,
            store_name=o.store_name,
            customer_name=o.customer_name,
            order_date=o.order_date,
            total_amount=_round_dec(o.total_amount),
            status=o.status,
        )
        for o in recent_order_rows
    ]

    return DashboardOverviewResponse(
        total_revenue=total_revenue,
        total_profit=total_profit,
        total_orders=total_orders,
        total_customers=total_customers,
        average_order_value=aov,
        gross_margin_pct=gross_margin_pct,
        revenue_growth_pct=rev_growth,
        profit_growth_pct=prof_growth,
        orders_growth_pct=orders_growth,
        top_products=top_products,
        top_stores=top_stores,
        category_distribution=category_dist,
        recent_orders=recent_orders,
        period=f"{start_date.isoformat() if start_date else 'All'} to {end_date.isoformat() if end_date else 'Now'}",
        start_date=start_date,
        end_date=end_date,
    )


def get_sales_trend(
    db: Session,
    interval: str = "monthly",
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> SalesTrendResponse:
    """
    Groups historical sales into time buckets:
    - daily (YYYY-MM-DD)
    - weekly (YYYY-Www)
    - monthly (YYYY-MM)
    """
    valid_intervals = {"daily": "day", "weekly": "week", "monthly": "month"}
    trunc_unit = valid_intervals.get(interval.lower(), "month")

    query = db.query(Sale)
    if start_date:
        query = query.filter(Sale.sale_date >= start_date)
    if end_date:
        query = query.filter(Sale.sale_date <= end_date)

    date_bucket = func.date_trunc(trunc_unit, Sale.sale_date)

    trend_rows = (
        query.with_entities(
            date_bucket.label("bucket"),
            func.sum(Sale.revenue).label("revenue"),
            func.sum(Sale.gross_profit).label("profit"),
            func.count(distinct(Sale.order_id)).label("orders_count"),
            func.sum(Sale.quantity).label("units_sold"),
        )
        .group_by(date_bucket)
        .order_by(date_bucket)
        .all()
    )

    points: List[SalesTrendPoint] = []
    tot_rev = Decimal("0.00")
    tot_prof = Decimal("0.00")

    for r in trend_rows:
        rev = _round_dec(r.revenue)
        prof = _round_dec(r.profit)
        orders = int(r.orders_count or 0)
        units = int(r.units_sold or 0)
        aov = _round_dec(rev / Decimal(orders)) if orders > 0 else Decimal("0.00")

        # Period label formatting
        dt: datetime = r.bucket
        if trunc_unit == "day":
            period_str = dt.strftime("%Y-%m-%d")
        elif trunc_unit == "week":
            period_str = dt.strftime("%Y-W%W")
        else:
            period_str = dt.strftime("%Y-%m")

        tot_rev += rev
        tot_prof += prof

        points.append(
            SalesTrendPoint(
                period=period_str,
                revenue=rev,
                profit=prof,
                orders_count=orders,
                units_sold=units,
                average_order_value=aov,
            )
        )

    return SalesTrendResponse(
        interval=interval,
        start_date=start_date,
        end_date=end_date,
        total_revenue=_round_dec(tot_rev),
        total_profit=_round_dec(tot_prof),
        points=points,
    )