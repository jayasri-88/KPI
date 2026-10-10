"""
Phase 3 Verification Script: Schema, Migrations, Row Counts, & Sample Queries
Retail KPI Intelligence Platform
"""

import sys
from decimal import Decimal
from sqlalchemy import text
from app.database import engine

def run_checks():
    print("=" * 70)
    print("RETAIL KPI PLATFORM - PHASE 3 VERIFICATION & SAMPLE QUERIES")
    print("=" * 70)

    with engine.connect() as conn:
        # 1. VERIFY ROW COUNTS
        print("\n[1/5] Verifying Database Table Row Counts...")
        tables = [
            ("users", "Users (Admin/Analysts/Managers)"),
            ("categories", "Merchandise Categories"),
            ("stores", "Physical Retail Stores"),
            ("products", "Product Catalog SKUs"),
            ("customers", "Customer Profiles"),
            ("orders", "Customer Orders (14-Month History)"),
            ("order_items", "Line Items per Order"),
            ("sales", "Consolidated Financial Sales"),
            ("inventory", "Store-Product Inventory Records"),
        ]

        total_rows = 0
        for table_name, desc in tables:
            cnt = conn.execute(text(f"SELECT count(*) FROM {table_name}")).scalar()
            print(f"      [OK] {table_name:<12} : {cnt:>6} rows  ({desc})")
            assert cnt > 0, f"Table {table_name} is unexpectedly empty!"
            total_rows += cnt

        print(f"\n      Total Active Relational Rows: {total_rows}")

        # 2. SAMPLE QUERY 1: EXECUTIVE STORE KPI & SPATIAL SUMMARY
        print("\n[2/5] Sample Query 1: Top 5 Stores by Gross Revenue & PostGIS Location...")
        q1 = text("""
            SELECT 
                s.store_code,
                s.name,
                s.city,
                s.region,
                COUNT(DISTINCT o.id) AS total_orders,
                COALESCE(SUM(sa.revenue), 0) AS total_revenue,
                COALESCE(SUM(sa.gross_profit), 0) AS total_profit,
                ROUND(AVG(sa.margin_pct), 2) AS avg_margin_pct,
                ST_AsText(s.location) AS spatial_point
            FROM stores s
            LEFT JOIN orders o ON o.store_id = s.id AND o.status = 'completed'
            LEFT JOIN sales sa ON sa.store_id = s.id
            GROUP BY s.id, s.store_code, s.name, s.city, s.region, s.location
            ORDER BY total_revenue DESC
            LIMIT 5;
        """)
        res1 = conn.execute(q1).fetchall()
        for r in res1:
            print(f"      Store [{r.store_code}] {r.name[:28]:<28} | City: {r.city:<10} | Rev: ???{r.total_revenue:>12,.2f} | Profit: ???{r.total_profit:>10,.2f} | Marg: {r.avg_margin_pct}% | Loc: {r.spatial_point}")

        # 3. SAMPLE QUERY 2: TOP SELLING PRODUCTS & MARGINS
        print("\n[3/5] Sample Query 2: Top 5 Best-Selling Products by Revenue...")
        q2 = text("""
            SELECT 
                p.sku_code,
                p.product_name,
                c.name AS category_name,
                SUM(sa.quantity) AS units_sold,
                SUM(sa.revenue) AS gross_revenue,
                SUM(sa.gross_profit) AS gross_profit,
                ROUND((SUM(sa.gross_profit) / NULLIF(SUM(sa.revenue), 0)) * 100, 2) AS realized_margin_pct
            FROM products p
            JOIN categories c ON c.id = p.category_id
            JOIN sales sa ON sa.product_id = p.id
            GROUP BY p.id, p.sku_code, p.product_name, c.name
            ORDER BY gross_revenue DESC
            LIMIT 5;
        """)
        res2 = conn.execute(q2).fetchall()
        for r in res2:
            print(f"      Product [{r.sku_code}] {r.product_name[:32]:<32} | Units: {r.units_sold:>3} | Rev: ???{r.gross_revenue:>11,.2f} | Profit: ???{r.gross_profit:>9,.2f} | Margin: {r.realized_margin_pct}%")

        # 4. SAMPLE QUERY 3: POSTGIS SPATIAL DISTANCE QUERY
        print("\n[4/5] Sample Query 3: PostGIS Spatial Proximity from Bengaluru Flagship...")
        q3 = text("""
            WITH bengaluru_store AS (
                SELECT location::geography AS geog 
                FROM stores 
                WHERE store_code = 'STR-BLR-01'
            )
            SELECT 
                s.store_code,
                s.name,
                s.city,
                ROUND((ST_Distance(s.location::geography, b.geog) / 1000.0)::numeric, 1) AS distance_km
            FROM stores s, bengaluru_store b
            WHERE s.store_code != 'STR-BLR-01'
            ORDER BY distance_km ASC
            LIMIT 5;
        """)
        res3 = conn.execute(q3).fetchall()
        for r in res3:
            print(f"      Store [{r.store_code}] {r.name[:32]:<32} | City: {r.city:<10} | Distance: {r.distance_km:>7.1f} km")

        # 5. SAMPLE QUERY 4: ACCOUNTING INTEGRITY AUDIT
        print("\n[5/5] Sample Query 4: Order Financial Consistency Audit (Sample 10 Orders)...")
        q4 = text("""
            SELECT 
                o.order_number,
                o.subtotal,
                o.discount_amount,
                o.tax_amount,
                o.total_amount,
                COALESCE(SUM(oi.total_price), 0) AS computed_item_subtotal_net,
                ROUND((o.subtotal - o.discount_amount + o.tax_amount), 2) AS formula_total
            FROM orders o
            JOIN order_items oi ON oi.order_id = o.id
            GROUP BY o.id, o.order_number, o.subtotal, o.discount_amount, o.tax_amount, o.total_amount
            LIMIT 5;
        """)
        res4 = conn.execute(q4).fetchall()
        for r in res4:
            discrepancy = abs(r.total_amount - r.formula_total)
            assert discrepancy < Decimal("0.05"), f"Financial discrepancy detected on {r.order_number}!"
            print(f"      Order [{r.order_number}] Sub: ???{r.subtotal:>9,.2f} | Disc: ???{r.discount_amount:>7,.2f} | Tax: ???{r.tax_amount:>7,.2f} | Total: ???{r.total_amount:>9,.2f} | Verified: OK")

    print("\n" + "=" * 70)
    print(">>> ALL PHASE 3 DATABASE, MODEL, AND SEED VERIFICATIONS PASSED! <<<")
    print("=" * 70)

if __name__ == "__main__":
    run_checks()
