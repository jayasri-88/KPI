"""
Analytics Tools for AI Retail Analyst
Implements 8 database-backed, parameterized tools for LangGraph.
Zero arbitrary SQL generation: all tools query through secure SQLAlchemy ORM/services.
"""

from datetime import datetime, timedelta
from decimal import Decimal
from typing import Any, Dict, List, Optional
from langchain_core.tools import tool
from sqlalchemy import func, desc, or_

from app.database import SessionLocal
from app.models import Customer, Order, OrderItem, Product, Sale, Store
from app.services import analytics_service, customer_service, dashboard_service, store_service
from ml.data_loader import load_daily_sales
from ml.forecaster import get_forecast


def _format_curr(val: float | Decimal) -> str:
    return f"INR {float(val):,.2f}"


@tool
def get_sales_kpi(
    region: Optional[str] = None,
    start_date: Optional[str] = None,
    end_date: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves overall commercial retail KPIs from the PostgreSQL database,
    including total revenue, gross profit, order count, customer count,
    average order value (AOV), and gross margin percentage.
    Optionally filter by region (North, South, West, East) or date range (YYYY-MM-DD).
    """
    db = SessionLocal()
    try:
        s_date = datetime.strptime(start_date, "%Y-%m-%d") if start_date else None
        e_date = datetime.strptime(end_date, "%Y-%m-%d") if end_date else None

        overview = dashboard_service.get_dashboard_kpis(
            db=db,
            start_date=s_date,
            end_date=e_date,
        )

        return {
            "period": overview.period,
            "total_revenue": float(overview.total_revenue),
            "total_revenue_formatted": _format_curr(overview.total_revenue),
            "total_profit": float(overview.total_profit),
            "total_profit_formatted": _format_curr(overview.total_profit),
            "gross_margin_pct": float(overview.gross_margin_pct),
            "total_orders": overview.total_orders,
            "total_customers": overview.total_customers,
            "average_order_value": float(overview.average_order_value),
            "average_order_value_formatted": _format_curr(overview.average_order_value),
            "revenue_growth_pct": float(overview.revenue_growth_pct),
            "profit_growth_pct": float(overview.profit_growth_pct),
        }
    finally:
        db.close()


@tool
def get_store_performance(
    region: Optional[str] = None,
    store_name: Optional[str] = None,
    sort_by: str = "revenue",
    limit: int = 10,
) -> Dict[str, Any]:
    """
    Ranks physical stores and returns financial metrics: revenue, gross profit,
    profit margin %, order count, target monthly sales, and target achievement %.
    Use this to identify top or underperforming retail stores across the network.
    """
    db = SessionLocal()
    try:
        # Defensive parameter clamping
        safe_limit = max(1, min(int(limit), 50))
        safe_region = region.strip()[:50] if region else None

        stores_perf = store_service.get_stores_performance(db=db, region=safe_region)

        # Filter by name if provided
        if store_name:
            q = store_name.strip()[:100].lower()
            stores_perf = [
                s for s in stores_perf
                if q in s.name.lower() or q in s.city.lower() or q in s.store_code.lower()
            ]

        # Sorting
        if sort_by == "margin":
            stores_perf.sort(key=lambda s: float(s.profit_margin_pct), reverse=True)
        elif sort_by == "target_achievement":
            stores_perf.sort(key=lambda s: float(s.target_achievement_pct), reverse=True)
        else:
            stores_perf.sort(key=lambda s: float(s.total_revenue), reverse=True)

        sliced = stores_perf[:safe_limit]
        results = []
        for s in sliced:
            results.append({
                "store_code": s.store_code,
                "name": s.name,
                "city": s.city,
                "region": s.region,
                "store_type": s.store_type,
                "total_revenue": float(s.total_revenue),
                "total_revenue_formatted": _format_curr(s.total_revenue),
                "total_profit": float(s.total_profit),
                "total_profit_formatted": _format_curr(s.total_profit),
                "profit_margin_pct": float(s.profit_margin_pct),
                "total_orders": s.total_orders,
                "average_order_value": float(s.average_order_value),
                "target_monthly_sales": float(s.target_monthly_sales),
                "target_achievement_pct": float(s.target_achievement_pct),
            })

        return {
            "total_stores_found": len(stores_perf),
            "stores": results,
            "top_store": results[0]["name"] if results else None,
            "bottom_store": results[-1]["name"] if results else None,
        }
    finally:
        db.close()


@tool
def get_product_performance(
    category_name: Optional[str] = None,
    limit: int = 10,
    order: str = "desc",
) -> Dict[str, Any]:
    """
    Retrieves product SKU performance rankings and Pareto 80/20 ABC classification.
    To find best-sellers, use order='desc'.
    To find low-performing or poorly performing products, use order='asc'.
    """
    db = SessionLocal()
    try:
        # Defensive parameter clamping
        safe_limit = max(1, min(int(limit), 50))
        analytics = analytics_service.get_product_performance_analytics(db=db, limit=100)
        products = analytics.products

        if category_name:
            cat_q = category_name.strip()[:100].lower()
            products = [p for p in products if cat_q in p.category_name.lower()]

        # Sort ascending or descending by revenue
        reverse = (order.strip().lower() == "desc")
        products.sort(key=lambda p: float(p.total_revenue), reverse=reverse)
        sliced = products[:safe_limit]

        results = []
        for p in sliced:
            results.append({
                "sku_code": p.sku_code,
                "product_name": p.product_name,
                "brand": p.brand,
                "category_name": p.category_name,
                "unit_price": p.unit_price,
                "units_sold": p.units_sold,
                "total_revenue": p.total_revenue,
                "total_revenue_formatted": _format_curr(p.total_revenue),
                "total_profit": p.total_profit,
                "margin_pct": p.margin_pct,
                "pareto_class": p.pareto_class,
                "revenue_share_pct": p.revenue_share_pct,
            })

        return {
            "total_skus_analyzed": analytics.total_skus_analyzed,
            "pareto_summary": analytics.pareto_summary,
            "products": results,
        }
    finally:
        db.close()


@tool
def get_customer_metrics() -> Dict[str, Any]:
    """
    Retrieves customer analytics, including total active customers,
    repeat customer count, repeat purchase rate %, average order value,
    and distribution across customer segments (VIP, Frequent, Occasional, One-Time).
    """
    db = SessionLocal()
    try:
        overview = customer_service.get_customer_overview(db=db)
        segments = customer_service.get_customer_segments(db=db)

        return {
            "total_customers": overview.total_customers,
            "active_customers": overview.active_customers,
            "repeat_customers": overview.repeat_customers,
            "repeat_customer_rate_pct": float(overview.repeat_customer_rate_pct),
            "average_orders_per_customer": float(overview.average_orders_per_customer),
            "average_revenue_per_customer": float(overview.average_revenue_per_customer),
            "average_revenue_per_customer_formatted": _format_curr(overview.average_revenue_per_customer),
            "segments": [
                {
                    "segment": s.segment,
                    "customer_count": s.customer_count,
                    "share_pct": float(s.share_pct),
                    "total_revenue": float(s.total_revenue),
                    "avg_order_value": float(s.avg_order_value),
                }
                for s in segments
            ],
        }
    finally:
        db.close()


@tool
def get_sales_trend(
    days: int = 90,
    store_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Retrieves recent sales trajectory, 7-day and 30-day moving averages,
    day-of-week seasonality (average trading volume on Monday through Sunday),
    historical peak day, and daily volatility (standard deviation).
    """
    db = SessionLocal()
    try:
        safe_days = max(7, min(int(days), 365))
        store_id = None
        if store_name:
            clean_store = store_name.strip()[:100].lower()
            store = (
                db.query(Store)
                .filter(
                    or_(
                        func.lower(Store.name).like(f"%{clean_store}%"),
                        func.lower(Store.city).like(f"%{clean_store}%"),
                    )
                )
                .first()
            )
            if store:
                store_id = str(store.id)

        trend = analytics_service.get_sales_trend_analytics(db=db, store_id=store_id, days=safe_days)

        return {
            "period_days": safe_days,
            "total_revenue": trend.total_revenue,
            "total_revenue_formatted": _format_curr(trend.total_revenue),
            "avg_daily_revenue": trend.avg_daily_revenue,
            "avg_daily_revenue_formatted": _format_curr(trend.avg_daily_revenue),
            "peak_day": trend.peak_day,
            "peak_day_revenue": trend.peak_day_revenue,
            "peak_day_revenue_formatted": _format_curr(trend.peak_day_revenue),
            "daily_volatility_std": trend.volatility_std,
            "day_of_week_seasonality": [
                {
                    "day": d.day_name,
                    "avg_revenue": d.avg_revenue,
                    "avg_orders": d.avg_orders,
                    "share_pct": d.share_pct,
                }
                for d in trend.day_of_week_pattern
            ],
        }
    finally:
        db.close()


@tool
def forecast_sales(
    days: int = 30,
    store_name: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Generates forward-looking sales demand forecasts for 7 or 30 days using Meta Prophet.
    Returns projected total revenue, daily expected sales with 80% confidence intervals,
    and out-of-time evaluation metrics (MAE, RMSE, WAPE).
    """
    db = SessionLocal()
    try:
        safe_days = max(1, min(int(days), 90))
        store_id = None
        target_name = "Network Total"
        if store_name:
            clean_store = store_name.strip()[:100].lower()
            store = (
                db.query(Store)
                .filter(
                    or_(
                        func.lower(Store.name).like(f"%{clean_store}%"),
                        func.lower(Store.city).like(f"%{clean_store}%"),
                    )
                )
                .first()
            )
            if store:
                store_id = str(store.id)
                target_name = f"{store.name} ({store.city})"

        df = load_daily_sales(db, store_id=store_id)
        if df.empty or len(df) < 14:
            return {"error": "Insufficient historical data for forecasting."}

        fc = get_forecast(df, horizon_days=safe_days, store_id=store_id, force_retrain=False)

        forecast_points = [
            {
                "date": p["date"],
                "forecast_sales": p["forecast_sales"],
                "lower_bound": p["lower_bound"],
                "upper_bound": p["upper_bound"],
            }
            for p in fc["forecast_data"]
        ]

        return {
            "target": target_name,
            "horizon_days": safe_days,
            "model_name": fc["model_name"],
            "total_projected_revenue": fc["total_forecast_revenue"],
            "total_projected_revenue_formatted": _format_curr(fc["total_forecast_revenue"]),
            "avg_daily_projected_sales": fc["avg_daily_forecast"],
            "avg_daily_projected_sales_formatted": _format_curr(fc["avg_daily_forecast"]),
            "evaluation_metrics": fc["evaluation_metrics"],
            "first_week_predictions": forecast_points[:7],
        }
    finally:
        db.close()


@tool
def compare_stores(
    store_a: str,
    store_b: str,
) -> Dict[str, Any]:
    """
    Performs a head-to-head financial comparison between two stores (e.g. 'Mumbai' vs 'Hyderabad' or 'Indiranagar' vs 'Bandra').
    Returns side-by-side revenue, profit, margin %, order volume, AOV, store size, and target achievement %.
    """
    db = SessionLocal()
    try:
        clean_a = store_a.strip()[:100]
        clean_b = store_b.strip()[:100]
        all_stores = store_service.get_stores_performance(db=db)

        def find_store(term: str):
            t = term.strip().lower()
            for s in all_stores:
                if t in s.name.lower() or t in s.city.lower() or t in s.store_code.lower():
                    return s
            return None

        st_a = find_store(clean_a)
        st_b = find_store(clean_b)

        available_cities = list(set(s.city for s in all_stores))

        if not st_a or not st_b:
            missing = []
            if not st_a:
                missing.append(f"'{clean_a}'")
            if not st_b:
                missing.append(f"'{clean_b}'")
            return {
                "error": f"Store {', '.join(missing)} was not found.",
                "available_store_cities": available_cities,
            }

        # Calculate metrics
        rev_a = float(st_a.total_revenue)
        rev_b = float(st_b.total_revenue)
        margin_a = float(st_a.profit_margin_pct)
        margin_b = float(st_b.profit_margin_pct)
        achieve_a = float(st_a.target_achievement_pct)
        achieve_b = float(st_b.target_achievement_pct)

        return {
            "store_1": {
                "code": st_a.store_code,
                "name": st_a.name,
                "city": st_a.city,
                "region": st_a.region,
                "type": st_a.store_type,
                "total_revenue": rev_a,
                "total_revenue_formatted": _format_curr(rev_a),
                "total_profit": float(st_a.total_profit),
                "profit_margin_pct": margin_a,
                "orders_count": st_a.total_orders,
                "average_order_value": float(st_a.average_order_value),
                "target_achievement_pct": achieve_a,
            },
            "store_2": {
                "code": st_b.store_code,
                "name": st_b.name,
                "city": st_b.city,
                "region": st_b.region,
                "type": st_b.store_type,
                "total_revenue": rev_b,
                "total_revenue_formatted": _format_curr(rev_b),
                "total_profit": float(st_b.total_profit),
                "profit_margin_pct": margin_b,
                "orders_count": st_b.total_orders,
                "average_order_value": float(st_b.average_order_value),
                "target_achievement_pct": achieve_b,
            },
            "comparison_summary": {
                "higher_revenue": st_a.name if rev_a > rev_b else st_b.name,
                "revenue_difference": abs(rev_a - rev_b),
                "higher_margin": st_a.name if margin_a > margin_b else st_b.name,
                "higher_target_achievement": st_a.name if achieve_a > achieve_b else st_b.name,
            },
        }
    finally:
        db.close()


@tool
def compare_periods(
    period_type: str = "month",
) -> Dict[str, Any]:
    """
    Compares sales between the most recent 30 days and the preceding 30 days.
    Explains the percentage variance, revenue delta, order count delta, and primary drivers.
    Answers questions like: 'Why did revenue fall or rise last month?'
    """
    db = SessionLocal()
    try:
        # Determine latest sale date
        latest_date_res = db.query(func.max(Sale.sale_date)).scalar()
        if not latest_date_res:
            return {"error": "No sales data found to compare periods."}

        end_recent = latest_date_res
        start_recent = end_recent - timedelta(days=30)
        end_prior = start_recent
        start_prior = end_prior - timedelta(days=30)

        # Recent period metrics
        rec_query = (
            db.query(
                func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("rev"),
                func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("prof"),
                func.count(func.distinct(Sale.order_id)).label("orders"),
            )
            .filter(Sale.sale_date >= start_recent, Sale.sale_date <= end_recent)
            .first()
        )

        # Prior period metrics
        prior_query = (
            db.query(
                func.coalesce(func.sum(Sale.revenue), Decimal("0.00")).label("rev"),
                func.coalesce(func.sum(Sale.gross_profit), Decimal("0.00")).label("prof"),
                func.count(func.distinct(Sale.order_id)).label("orders"),
            )
            .filter(Sale.sale_date >= start_prior, Sale.sale_date < end_prior)
            .first()
        )

        rec_rev = float(rec_query.rev)
        prior_rev = float(prior_query.rev)
        rec_orders = int(rec_query.orders)
        prior_orders = int(prior_query.orders)

        rev_delta = rec_rev - prior_rev
        rev_growth_pct = ((rev_delta / prior_rev) * 100.0) if prior_rev > 0 else 0.0

        orders_delta = rec_orders - prior_orders
        orders_growth_pct = ((orders_delta / prior_orders) * 100.0) if prior_orders > 0 else 0.0

        rec_aov = (rec_rev / rec_orders) if rec_orders > 0 else 0.0
        prior_aov = (prior_rev / prior_orders) if prior_orders > 0 else 0.0
        aov_growth_pct = (((rec_aov - prior_aov) / prior_aov) * 100.0) if prior_aov > 0 else 0.0

        return {
            "recent_period": {
                "start": start_recent.strftime("%Y-%m-%d"),
                "end": end_recent.strftime("%Y-%m-%d"),
                "revenue": rec_rev,
                "revenue_formatted": _format_curr(rec_rev),
                "orders": rec_orders,
                "average_order_value": round(rec_aov, 2),
            },
            "prior_period": {
                "start": start_prior.strftime("%Y-%m-%d"),
                "end": end_prior.strftime("%Y-%m-%d"),
                "revenue": prior_rev,
                "revenue_formatted": _format_curr(prior_rev),
                "orders": prior_orders,
                "average_order_value": round(prior_aov, 2),
            },
            "variance": {
                "revenue_delta": round(rev_delta, 2),
                "revenue_growth_pct": round(rev_growth_pct, 2),
                "orders_delta": orders_delta,
                "orders_growth_pct": round(orders_growth_pct, 2),
                "aov_growth_pct": round(aov_growth_pct, 2),
                "primary_driver": (
                    "Decline in transaction order volume" if orders_growth_pct < aov_growth_pct
                    else "Decline in average basket value (AOV)"
                ) if rev_delta < 0 else (
                    "Surge in transaction volume" if orders_growth_pct > aov_growth_pct
                    else "Increase in basket size (AOV)"
                ),
            },
        }
    finally:
        db.close()


ALL_TOOLS = [
    get_sales_kpi,
    get_store_performance,
    get_product_performance,
    get_customer_metrics,
    get_sales_trend,
    forecast_sales,
    compare_stores,
    compare_periods,
]
