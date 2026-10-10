"""
Analytics Service Module
Performs time-series trends, moving averages, day-of-week patterns,
category demand analytics, and SKU Pareto distribution using Pandas and NumPy.
"""

from typing import Dict, List, Optional
import numpy as np
import pandas as pd
from sqlalchemy.orm import Session

from app.schemas import (
    CategoryDemandItem,
    DayOfWeekPattern,
    DemandAnalyticsResponse,
    ProductPerformanceAnalyticsResponse,
    ProductPerformanceItem,
    SalesTrendAnalyticsResponse,
    SalesTrendPoint,
)
from ml.data_loader import load_category_demand, load_daily_sales, load_product_performance

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def get_sales_trend_analytics(
    db: Session,
    store_id: Optional[str] = None,
    days: int = 90,
) -> SalesTrendAnalyticsResponse:
    """
    Computes rolling moving averages (7-day MA, 30-day MA),
    day-of-week seasonality, peak sales day, and volatility metrics.
    """
    df = load_daily_sales(db, store_id=store_id)
    if df.empty:
        return SalesTrendAnalyticsResponse(
            points=[],
            day_of_week_pattern=[],
            total_revenue=0.0,
            avg_daily_revenue=0.0,
            peak_day="N/A",
            peak_day_revenue=0.0,
            volatility_std=0.0,
        )

    # Compute Moving Averages on entire history
    df["ma_7"] = df["y"].rolling(window=7, min_periods=1).mean()
    df["ma_30"] = df["y"].rolling(window=30, min_periods=1).mean()

    # Day of week seasonality analysis
    df["dow"] = df["ds"].dt.dayofweek
    dow_summary = df.groupby("dow").agg(
        avg_revenue=("y", "mean"),
        avg_orders=("order_count", "mean"),
        total_rev=("y", "sum"),
    ).reset_index()

    total_dow_rev = dow_summary["total_rev"].sum()
    dow_patterns: List[DayOfWeekPattern] = []
    for _, r in dow_summary.iterrows():
        d_idx = int(r["dow"])
        share = (float(r["total_rev"]) / total_dow_rev * 100.0) if total_dow_rev > 0 else 0.0
        dow_patterns.append(
            DayOfWeekPattern(
                day_name=DAY_NAMES[d_idx],
                day_idx=d_idx,
                avg_revenue=round(float(r["avg_revenue"]), 2),
                avg_orders=round(float(r["avg_orders"]), 1),
                share_pct=round(share, 2),
            )
        )

    # Slice recent days for the detailed trend points
    recent_df = df.tail(days).copy()
    points: List[SalesTrendPoint] = []
    for _, row in recent_df.iterrows():
        points.append(
            SalesTrendPoint(
                date=row["ds"].strftime("%Y-%m-%d"),
                revenue=round(float(row["y"]), 2),
                profit=round(float(row["gross_profit"]), 2),
                orders=int(row["order_count"]),
                ma_7=round(float(row["ma_7"]), 2) if not pd.isna(row["ma_7"]) else None,
                ma_30=round(float(row["ma_30"]), 2) if not pd.isna(row["ma_30"]) else None,
            )
        )

    total_rev = float(recent_df["y"].sum())
    avg_daily = float(recent_df["y"].mean()) if not recent_df.empty else 0.0
    volatility = float(recent_df["y"].std()) if len(recent_df) > 1 else 0.0

    peak_row = recent_df.loc[recent_df["y"].idxmax()] if not recent_df.empty else None
    peak_date = peak_row["ds"].strftime("%Y-%m-%d") if peak_row is not None else "N/A"
    peak_rev = float(peak_row["y"]) if peak_row is not None else 0.0

    return SalesTrendAnalyticsResponse(
        points=points,
        day_of_week_pattern=dow_patterns,
        total_revenue=round(total_rev, 2),
        avg_daily_revenue=round(avg_daily, 2),
        peak_day=peak_date,
        peak_day_revenue=round(peak_rev, 2),
        volatility_std=round(volatility, 2),
    )


def get_demand_analytics(db: Session) -> DemandAnalyticsResponse:
    """
    Computes cross-category retail demand and volume velocity.
    """
    df = load_category_demand(db)
    if df.empty:
        return DemandAnalyticsResponse(
            categories=[],
            total_units_sold=0,
            total_revenue=0.0,
            top_category_name="N/A",
        )

    total_rev = float(df["total_revenue"].sum())
    total_units = int(df["total_units_sold"].sum())

    categories: List[CategoryDemandItem] = []
    for _, row in df.iterrows():
        cat_rev = float(row["total_revenue"])
        share = (cat_rev / total_rev * 100.0) if total_rev > 0 else 0.0
        categories.append(
            CategoryDemandItem(
                category_name=str(row["category_name"]),
                category_code=str(row["category_code"]),
                sku_count=int(row["sku_count"]),
                total_units_sold=int(row["total_units_sold"]),
                total_revenue=round(cat_rev, 2),
                total_profit=round(float(row["total_profit"]), 2),
                avg_selling_price=round(float(row["avg_selling_price"]), 2),
                revenue_share_pct=round(share, 2),
            )
        )

    top_cat = categories[0].category_name if categories else "N/A"
    return DemandAnalyticsResponse(
        categories=categories,
        total_units_sold=total_units,
        total_revenue=round(total_rev, 2),
        top_category_name=top_cat,
    )


def get_product_performance_analytics(
    db: Session, limit: int = 50
) -> ProductPerformanceAnalyticsResponse:
    """
    Performs SKU-level Pareto 80/20 ABC classification and margin analysis.
    """
    df = load_product_performance(db, limit=limit)
    if df.empty:
        return ProductPerformanceAnalyticsResponse(
            products=[],
            total_skus_analyzed=0,
            pareto_summary={"Class A (Top 80%)": 0, "Class B (80-95%)": 0, "Class C (Tail 5%)": 0},
        )

    products: List[ProductPerformanceItem] = []
    pareto_counts = {"Class A (Top 80%)": 0, "Class B (80-95%)": 0, "Class C (Tail 5%)": 0}

    for _, row in df.iterrows():
        rev = float(row["total_revenue"])
        prof = float(row["total_profit"])
        margin = (prof / rev * 100.0) if rev > 0 else 0.0
        p_class = str(row["pareto_class"])
        pareto_counts[p_class] = pareto_counts.get(p_class, 0) + 1

        products.append(
            ProductPerformanceItem(
                product_id=row["product_id"],
                sku_code=str(row["sku_code"]),
                product_name=str(row["product_name"]),
                brand=str(row["brand"]),
                category_name=str(row["category_name"]),
                unit_price=round(float(row["unit_price"]), 2),
                cost_price=round(float(row["cost_price"]), 2),
                units_sold=int(row["units_sold"]),
                total_revenue=round(rev, 2),
                total_profit=round(prof, 2),
                margin_pct=round(margin, 2),
                revenue_share_pct=round(float(row["revenue_share_pct"]), 2),
                cumulative_revenue_pct=round(float(row["cumulative_revenue_pct"]), 2),
                pareto_class=p_class,
            )
        )

    return ProductPerformanceAnalyticsResponse(
        products=products,
        total_skus_analyzed=len(products),
        pareto_summary=pareto_counts,
    )