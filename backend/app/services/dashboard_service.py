"""Dashboard KPI service.

Business definitions (documented per senior-engineering rules; where the
repository defined no explicit rule, the choice below is the documented
rule):

* revenue            = SUM(order_items.total_price)   [GROSS, pre-discount:
                       matches the source `sales_transactions.revenue`
                       convention verified during ingestion]
* net revenue        = revenue - SUM(order discount)  [derived]
* units              = SUM(order_items.quantity)
* transactions       = orders with >= 1 line          [not a bare row count:
                       line-less orders are excluded everywhere]
* cancelled orders   = Orders with status = 'cancelled' are excluded from
                       ALL monetary and count KPIs. (No product spec defines
                       this; excluding cancelled sales is the reasonable
                       retail rule and is covered by tests.)
* avg_discount       = simple mean of line discount_percent
* profit             = SUM(quantity * (unit_price - product.cost_price))
                       [GROSS-margin convention, consistent with revenue;
                       excludes shipping/fees, which the schema lacks]
* AOV                = revenue / transactions         [None if no orders]
* revenue growth     = (last_month - prev_month) / prev_month, on monthly
                       revenue series                  [None if not computable]
* category/region
  contribution       = category|region revenue / total revenue
"""
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Category, OrderItem, Order, Product, Store

CANCELLED = "cancelled"


def _base_order_filters():
    """Filters every order-derived KPI must apply (business rule)."""
    return [Order.status != CANCELLED]


def get_dashboard_overview() -> dict:
    db = SessionLocal()
    try:
        cancelled = _base_order_filters()

        # ---- Core KPIs over order lines (cancelled orders excluded) ----
        row = (
            db.query(
                func.coalesce(func.sum(OrderItem.total_price), 0.0).label("revenue"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units"),
                func.count(func.distinct(OrderItem.order_id)).label("transactions"),
                func.coalesce(func.avg(OrderItem.discount_percent), 0.0).label("avg_discount"),
                # Net line revenue = gross - discount applied to the line
                func.coalesce(
                    func.sum(
                        OrderItem.total_price * (1 - OrderItem.discount_percent / 100.0)
                    ),
                    0.0,
                ).label("net_revenue"),
            )
            .join(Order, OrderItem.order_id == Order.id)
            .filter(*cancelled)
            .one()
        )

        total_revenue = round(float(row.revenue), 2)
        total_units = int(row.units)
        total_transactions = int(row.transactions)
        avg_discount = round(float(row.avg_discount), 2)
        net_revenue = round(float(row.net_revenue), 2)

        # AOV = revenue / transactions (guard against division by zero).
        aov = round(total_revenue / total_transactions, 2) if total_transactions else None

        # ---- Profit: gross margin per line vs product cost ----
        profit_result = (
            db.query(
                func.coalesce(
                    func.sum(
                        OrderItem.quantity
                        * (OrderItem.unit_price - func.coalesce(Product.cost_price, 0.0))
                    ),
                    0.0,
                )
            )
            .join(Order, OrderItem.order_id == Order.id)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(*cancelled)
            .scalar()
        )
        total_profit = round(float(profit_result), 2)
        profit_margin = round(total_profit / total_revenue * 100, 2) if total_revenue else None

        # ---- Catalog sizes (not order-dependent) ----
        total_products = db.query(func.count(Product.id)).scalar()
        total_retailers = db.query(func.count(Store.id)).scalar()

        # ---- Top category + its contribution share ----
        top_category_result = (
            db.query(
                Category.name.label("category"),
                func.coalesce(func.sum(OrderItem.total_price), 0.0).label("revenue"),
            )
            .join(Product, Product.category_id == Category.id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .filter(*cancelled)
            .group_by(Category.id, Category.name)
            .order_by(func.sum(OrderItem.total_price).desc())
            .first()
        )
        top_category = top_category_result.category if top_category_result else None
        top_category_revenue = (
            round(float(top_category_result.revenue), 2) if top_category_result else 0.0
        )
        top_category_share = (
            round(top_category_revenue / total_revenue * 100, 2) if total_revenue else None
        )

        # ---- Top region + its contribution share ----
        top_region_result = (
            db.query(
                Store.region.label("region"),
                func.coalesce(func.sum(OrderItem.total_price), 0.0).label("revenue"),
            )
            .join(Order, Store.id == Order.store_id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .filter(*cancelled)
            .group_by(Store.region)
            .order_by(func.sum(OrderItem.total_price).desc())
            .first()
        )
        top_region = top_region_result.region if top_region_result else None
        top_region_revenue = (
            round(float(top_region_result.revenue), 2) if top_region_result else 0.0
        )
        top_region_share = (
            round(top_region_revenue / total_revenue * 100, 2) if total_revenue else None
        )

        # ---- Monthly series (cancelled excluded, months ordered asc) ----
        monthly_result = (
            db.query(
                func.to_char(Order.created_at, "YYYY-MM").label("month"),
                func.coalesce(func.sum(OrderItem.total_price), 0.0).label("revenue"),
                func.coalesce(
                    func.sum(
                        OrderItem.total_price * (1 - OrderItem.discount_percent / 100.0)
                    ),
                    0.0,
                ).label("net_revenue"),
                func.count(func.distinct(Order.id)).label("transactions"),
                func.coalesce(func.sum(OrderItem.quantity), 0).label("units"),
                func.coalesce(
                    func.sum(
                        OrderItem.quantity
                        * (OrderItem.unit_price - func.coalesce(Product.cost_price, 0.0))
                    ),
                    0.0,
                ).label("profit"),
            )
            .join(OrderItem, Order.id == OrderItem.order_id)
            .join(Product, OrderItem.product_id == Product.id)
            .filter(*cancelled)
            .group_by(func.to_char(Order.created_at, "YYYY-MM"))
            .order_by(func.to_char(Order.created_at, "YYYY-MM"))
            .all()
        )
        monthly_sales = [
            {
                "month": r.month,
                "revenue": round(float(r.revenue), 2),
                "net_revenue": round(float(r.net_revenue), 2),
                "profit": round(float(r.profit), 2),
                "transactions": int(r.transactions),
                "units": int(r.units),
                "aov": round(float(r.revenue) / int(r.transactions), 2)
                if int(r.transactions)
                else None,
            }
            for r in monthly_result
        ]

        # ---- Growth: last vs previous month on equivalent periods ----
        revenue_growth = None
        profit_growth = None
        if len(monthly_result) >= 2:
            prev, last = monthly_result[-2], monthly_result[-1]
            prev_rev, last_rev = float(prev.revenue), float(last.revenue)
            revenue_growth = (
                round((last_rev - prev_rev) / prev_rev * 100, 2) if prev_rev else None
            )
            prev_profit, last_profit = float(prev.profit), float(last.profit)
            profit_growth = (
                round((last_profit - prev_profit) / prev_profit * 100, 2)
                if prev_profit
                else None
            )

        return {
            "total_revenue": total_revenue,
            "net_revenue": net_revenue,
            "total_units": total_units,
            "total_transactions": total_transactions,
            "avg_order_value": aov,
            "total_profit": total_profit,
            "profit_margin": profit_margin,
            "avg_discount": avg_discount,
            "total_products": int(total_products) if total_products else 0,
            "total_retailers": int(total_retailers) if total_retailers else 0,
            "top_category": top_category or "N/A",
            "top_category_revenue": top_category_revenue,
            "top_category_share": top_category_share,
            "top_region": top_region or "N/A",
            "top_region_revenue": top_region_revenue,
            "top_region_share": top_region_share,
            "revenue_growth": revenue_growth,
            "profit_growth": profit_growth,
            "monthly_sales": monthly_sales,
        }
    finally:
        db.close()
