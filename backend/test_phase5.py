"""
Verification Suite for Phase 5: Complete REST API Layer
Tests all endpoints across Dashboard, Stores, Products, Categories,
Customers, Orders, Sales, and Inventory.
Verifies real-time calculations from PostgreSQL, pagination, filtering,
and authentication headers.
"""

import sys
import os
from decimal import Decimal
from starlette.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)


def test_phase5_rest_apis():
    print("=" * 70)
    print("RETAIL KPI INTELLIGENCE PLATFORM - PHASE 5 REST API VERIFICATION SUITE")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # STEP 0: Authenticate to obtain Bearer Token
    # -------------------------------------------------------------------------
    print("\n[STEP 0] Authenticating as Analyst to acquire JWT Bearer token...")
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst@retailkpi.com", "password": "Analyst@2026"},
    )
    assert login_res.status_code == 200, f"Analyst login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"      [OK] Token acquired: {token[:25]}...")

    # -------------------------------------------------------------------------
    # TEST 1: Dashboard Overview (GET /api/v1/dashboard/overview)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Testing Dashboard Overview (GET /api/v1/dashboard/overview)...")
    dash_res = client.get("/api/v1/dashboard/overview", headers=headers)
    assert dash_res.status_code == 200, f"Dashboard failed: {dash_res.text}"
    dash = dash_res.json()

    rev = Decimal(str(dash["total_revenue"]))
    prof = Decimal(str(dash["total_profit"]))
    orders = int(dash["total_orders"])
    customers = int(dash["total_customers"])
    aov = Decimal(str(dash["average_order_value"]))
    margin = Decimal(str(dash["gross_margin_pct"]))

    print(f"      - Total Revenue: INR {rev:,.2f}")
    print(f"      - Total Profit:  INR {prof:,.2f} ({margin}% Gross Margin)")
    print(f"      - Total Orders:  {orders:,}")
    print(f"      - Customers:     {customers:,}")
    print(f"      - AOV:           INR {aov:,.2f}")

    assert rev > Decimal("0.00"), "Total revenue must be greater than zero!"
    assert prof > Decimal("0.00"), "Total profit must be greater than zero!"
    assert orders >= 800, f"Expected ~850 orders, found {orders}"
    assert customers >= 50, f"Expected ~60 customers, found {customers}"
    assert len(dash["top_products"]) > 0, "Top products must not be empty!"
    assert len(dash["top_stores"]) > 0, "Top stores must not be empty!"
    assert len(dash["category_distribution"]) > 0, "Category distribution must not be empty!"
    assert len(dash["recent_orders"]) > 0, "Recent orders must not be empty!"
    print("      [PASS] Real-time PostgreSQL executive KPIs verified successfully.")

    # -------------------------------------------------------------------------
    # TEST 2: Sales Trend (GET /api/v1/dashboard/sales-trend)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing Sales Trend (GET /api/v1/dashboard/sales-trend)...")
    trend_res = client.get("/api/v1/dashboard/sales-trend?interval=monthly", headers=headers)
    assert trend_res.status_code == 200, f"Trend failed: {trend_res.text}"
    trend = trend_res.json()
    assert trend["interval"] == "monthly"
    assert len(trend["points"]) >= 12, f"Expected at least 12 months history, found {len(trend['points'])}"
    print(f"      [PASS] Aggregated {len(trend['points'])} monthly trend intervals. Latest: {trend['points'][-1]['period']} (INR {trend['points'][-1]['revenue']})")

    # -------------------------------------------------------------------------
    # TEST 3: Stores API (GET /api/v1/stores)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Testing Stores List & Pagination (GET /api/v1/stores)...")
    stores_res = client.get("/api/v1/stores?page=1&size=5", headers=headers)
    assert stores_res.status_code == 200
    st_data = stores_res.json()
    assert st_data["total"] >= 10, f"Expected 10 stores, got {st_data['total']}"
    assert len(st_data["items"]) == 5
    first_store = st_data["items"][0]
    assert "latitude" in first_store and "longitude" in first_store
    print(f"      [PASS] Retrieved {st_data['total']} stores. First: {first_store['name']} ({first_store['city']})")

    # -------------------------------------------------------------------------
    # TEST 4: Store Performance (GET /api/v1/stores/performance)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Testing Store Performance Rankings (GET /api/v1/stores/performance)...")
    perf_res = client.get("/api/v1/stores/performance", headers=headers)
    assert perf_res.status_code == 200
    perf_list = perf_res.json()
    assert len(perf_list) >= 10
    top_perf = perf_list[0]
    print(f"      [PASS] Top performing store: {top_perf['name']} with INR {top_perf['total_revenue']} revenue ({top_perf['target_achievement_pct']}% of target)")

    # -------------------------------------------------------------------------
    # TEST 5: Products API (GET /api/v1/products)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Testing Products Catalog & Filtering (GET /api/v1/products)...")
    prod_res = client.get("/api/v1/products?page=1&size=10&search=Pro", headers=headers)
    assert prod_res.status_code == 200
    prod_data = prod_res.json()
    assert prod_data["total"] > 0
    print(f"      [PASS] Product search 'Pro' matched {prod_data['total']} catalog SKUs.")

    # -------------------------------------------------------------------------
    # TEST 6: Categories API (GET /api/v1/categories)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Testing Categories API (GET /api/v1/categories)...")
    cat_res = client.get("/api/v1/categories", headers=headers)
    assert cat_res.status_code == 200
    cats = cat_res.json()
    assert len(cats) >= 6, f"Expected 6 departments, found {len(cats)}"
    cat_names = [c["name"] for c in cats]
    print(f"      [PASS] Verified {len(cats)} merchandise departments: {', '.join(cat_names[:4])}...")

    # -------------------------------------------------------------------------
    # TEST 7: Customers API (GET /api/v1/customers)
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Testing Customers Cohort Filtering (GET /api/v1/customers)...")
    cust_res = client.get("/api/v1/customers?segment=VIP", headers=headers)
    assert cust_res.status_code == 200
    vip_data = cust_res.json()
    assert vip_data["total"] > 0
    first_vip = vip_data["items"][0]
    assert first_vip["segment"] == "VIP"
    print(f"      [PASS] Found {vip_data['total']} VIP cohort customers. Top spend: INR {first_vip['total_spend']}")

    # -------------------------------------------------------------------------
    # TEST 8: Orders API (GET /api/v1/orders)
    # -------------------------------------------------------------------------
    print("\n[TEST 8] Testing Orders API & Details (GET /api/v1/orders)...")
    orders_res = client.get("/api/v1/orders?page=1&size=5", headers=headers)
    assert orders_res.status_code == 200
    ord_data = orders_res.json()
    assert ord_data["total"] >= 800
    sample_order_id = ord_data["items"][0]["id"]

    # Detail query
    detail_res = client.get(f"/api/v1/orders/{sample_order_id}", headers=headers)
    assert detail_res.status_code == 200
    order_detail = detail_res.json()
    assert len(order_detail["order_items"]) > 0
    print(f"      [PASS] Order {order_detail['order_number']}: Total INR {order_detail['total_amount']} with {len(order_detail['order_items'])} items.")

    # -------------------------------------------------------------------------
    # TEST 9: Sales API (GET /api/v1/sales)
    # -------------------------------------------------------------------------
    print("\n[TEST 9] Testing Sales Financial Ledger (GET /api/v1/sales)...")
    sales_res = client.get("/api/v1/sales?page=1&size=5", headers=headers)
    assert sales_res.status_code == 200
    s_data = sales_res.json()
    assert s_data["total"] >= 1000
    first_sale = s_data["items"][0]
    assert "revenue" in first_sale and "gross_profit" in first_sale and "margin_pct" in first_sale
    print(f"      [PASS] Verified {s_data['total']} sales records. Margin on first: {first_sale['margin_pct']}%")

    # -------------------------------------------------------------------------
    # TEST 10: Sales Summary (GET /api/v1/sales/summary)
    # -------------------------------------------------------------------------
    print("\n[TEST 10] Testing Sales Summary Aggregate (GET /api/v1/sales/summary)...")
    summ_res = client.get("/api/v1/sales/summary", headers=headers)
    assert summ_res.status_code == 200
    summary = summ_res.json()
    assert Decimal(str(summary["total_revenue"])) > Decimal("0.00")
    print(f"      [PASS] Consolidated Sales: INR {summary['total_revenue']} across {summary['total_orders']} orders.")

    # -------------------------------------------------------------------------
    # TEST 11: Inventory API (GET /api/v1/inventory)
    # -------------------------------------------------------------------------
    print("\n[TEST 11] Testing Inventory Stock Tracking (GET /api/v1/inventory)...")
    inv_res = client.get("/api/v1/inventory?page=1&size=5", headers=headers)
    assert inv_res.status_code == 200
    inv_data = inv_res.json()
    assert inv_data["total"] >= 300
    print(f"      [PASS] Multi-store inventory tracking {inv_data['total']} stock keeping records.")

    # -------------------------------------------------------------------------
    # TEST 12: Inventory Stock Alerts (GET /api/v1/inventory/alerts)
    # -------------------------------------------------------------------------
    print("\n[TEST 12] Testing Inventory Reorder Alerts (GET /api/v1/inventory/alerts)...")
    alerts_res = client.get("/api/v1/inventory/alerts", headers=headers)
    assert alerts_res.status_code == 200
    alerts = alerts_res.json()
    assert len(alerts) > 0
    first_alert = alerts[0]
    print(f"      [PASS] {len(alerts)} stock replenishment alerts detected! First: {first_alert['product_name']} at {first_alert['store_name']} ({first_alert['urgency']}, Deficit: {first_alert['deficit']} units)")

    print("\n" + "=" * 70)
    print("ALL 12 PHASE 5 REST API TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_phase5_rest_apis()
