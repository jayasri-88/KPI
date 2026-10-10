"""
Data Loader Module for Retail Analytics and ML
Extracts sales, demand, product, and store datasets from PostgreSQL.
"""

import os
from typing import Optional
import pandas as pd
from sqlalchemy import text
from sqlalchemy.orm import Session
from sqlalchemy.engine import Engine


def load_daily_sales(db_or_engine, store_id: Optional[str] = None) -> pd.DataFrame:
    """
    Extracts time series of daily aggregated retail sales.
    Fills missing dates with 0 so the time series has a strict daily frequency without gaps.
    """
    params = {}
    where_clause = ""
    if store_id:
        where_clause = "WHERE store_id = :store_id"
        params["store_id"] = str(store_id)

    query = f"""
        SELECT 
            DATE(sale_date) as ds,
            COALESCE(SUM(revenue), 0.0) as y,
            COALESCE(SUM(gross_profit), 0.0) as gross_profit,
            COALESCE(SUM(quantity), 0) as quantity,
            COUNT(DISTINCT order_id) as order_count
        FROM sales
        {where_clause}
        GROUP BY DATE(sale_date)
        ORDER BY ds ASC;
    """

    if isinstance(db_or_engine, Session):
        result = db_or_engine.execute(text(query), params).fetchall()
        df = pd.DataFrame(result, columns=["ds", "y", "gross_profit", "quantity", "order_count"])
    else:
        df = pd.read_sql(text(query), db_or_engine, params=params)

    if df.empty:
        return pd.DataFrame(columns=["ds", "y", "gross_profit", "quantity", "order_count"])

    df["ds"] = pd.to_datetime(df["ds"])
    df["y"] = pd.to_numeric(df["y"], errors="coerce").fillna(0.0)
    df["gross_profit"] = pd.to_numeric(df["gross_profit"], errors="coerce").fillna(0.0)
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").fillna(0)
    df["order_count"] = pd.to_numeric(df["order_count"], errors="coerce").fillna(0)

    # Reindex to full continuous daily frequency between min and max date
    full_idx = pd.date_range(start=df["ds"].min(), end=df["ds"].max(), freq="D", name="ds")
    df = df.set_index("ds").reindex(full_idx).fillna({
        "y": 0.0,
        "gross_profit": 0.0,
        "quantity": 0,
        "order_count": 0,
    }).reset_index()

    return df


def load_category_demand(db_or_engine, start_date=None, end_date=None) -> pd.DataFrame:
    """
    Extracts category-level demand, volume, and revenue metrics.
    """
    query = """
        SELECT 
            c.name as category_name,
            c.code as category_code,
            COUNT(DISTINCT p.id) as sku_count,
            COALESCE(SUM(s.quantity), 0) as total_units_sold,
            COALESCE(SUM(s.revenue), 0.0) as total_revenue,
            COALESCE(SUM(s.gross_profit), 0.0) as total_profit,
            AVG(COALESCE(s.unit_price, p.unit_price)) as avg_selling_price
        FROM categories c
        JOIN products p ON c.id = p.category_id
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY c.id, c.name, c.code
        ORDER BY total_revenue DESC;
    """
    if isinstance(db_or_engine, Session):
        result = db_or_engine.execute(text(query)).fetchall()
        df = pd.DataFrame(result, columns=[
            "category_name", "category_code", "sku_count",
            "total_units_sold", "total_revenue", "total_profit", "avg_selling_price"
        ])
    else:
        df = pd.read_sql(text(query), db_or_engine)

    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce").fillna(0.0)
    df["total_profit"] = pd.to_numeric(df["total_profit"], errors="coerce").fillna(0.0)
    df["total_units_sold"] = pd.to_numeric(df["total_units_sold"], errors="coerce").fillna(0)
    df["avg_selling_price"] = pd.to_numeric(df["avg_selling_price"], errors="coerce").fillna(0.0)
    return df


def load_product_performance(db_or_engine, limit: int = 50) -> pd.DataFrame:
    """
    Extracts SKU-level performance metrics and computes Pareto cumulative revenue %.
    """
    query = f"""
        SELECT 
            p.id as product_id,
            p.sku_code,
            p.product_name,
            p.brand,
            c.name as category_name,
            p.unit_price,
            p.cost_price,
            COALESCE(SUM(s.quantity), 0) as units_sold,
            COALESCE(SUM(s.revenue), 0.0) as total_revenue,
            COALESCE(SUM(s.gross_profit), 0.0) as total_profit,
            COUNT(DISTINCT s.order_id) as order_frequency
        FROM products p
        JOIN categories c ON p.category_id = c.id
        LEFT JOIN sales s ON p.id = s.product_id
        GROUP BY p.id, p.sku_code, p.product_name, p.brand, c.name, p.unit_price, p.cost_price
        ORDER BY total_revenue DESC
        LIMIT {limit};
    """
    if isinstance(db_or_engine, Session):
        result = db_or_engine.execute(text(query)).fetchall()
        df = pd.DataFrame(result, columns=[
            "product_id", "sku_code", "product_name", "brand",
            "category_name", "unit_price", "cost_price",
            "units_sold", "total_revenue", "total_profit", "order_frequency"
        ])
    else:
        df = pd.read_sql(text(query), db_or_engine)

    df["total_revenue"] = pd.to_numeric(df["total_revenue"], errors="coerce").fillna(0.0)
    df["total_profit"] = pd.to_numeric(df["total_profit"], errors="coerce").fillna(0.0)
    df["units_sold"] = pd.to_numeric(df["units_sold"], errors="coerce").fillna(0)

    # Compute Pareto Cumulative Share
    total_rev = df["total_revenue"].sum()
    if total_rev > 0:
        df["revenue_share_pct"] = (df["total_revenue"] / total_rev) * 100.0
        df["cumulative_revenue_pct"] = df["revenue_share_pct"].cumsum()
        df["pareto_class"] = df["cumulative_revenue_pct"].apply(
            lambda x: "Class A (Top 80%)" if x <= 80 else ("Class B (80-95%)" if x <= 95 else "Class C (Tail 5%)")
        )
    else:
        df["revenue_share_pct"] = 0.0
        df["cumulative_revenue_pct"] = 0.0
        df["pareto_class"] = "Class C"

    return df
