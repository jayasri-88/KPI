"""
Verification Suite for Phase 8: ML Analytics & Sales Forecasting
Tests sales trends (moving averages, seasonality), demand analytics,
product Pareto 80/20 analysis, store performance, and 7-day / 30-day Prophet forecasting.
"""

import sys
import os
from decimal import Decimal
from starlette.testclient import TestClient

# Add project root and backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)


def test_phase8_ml_and_forecasting():
    print("=" * 70)
    print("RETAIL KPI INTELLIGENCE PLATFORM - PHASE 8 ML & FORECASTING TEST")
    print("=" * 70)

    # -------------------------------------------------------------------------
    # STEP 0: Authentication
    # -------------------------------------------------------------------------
    print("\n[STEP 0] Authenticating to acquire JWT Bearer token...")
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "analyst@retailkpi.com", "password": "Analyst@2026"},
    )
    assert login_res.status_code == 200, f"Analyst login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"      [OK] Token acquired: {token[:25]}...")

    # -------------------------------------------------------------------------
    # TEST 1: Unauthenticated request should be rejected (401)
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Testing unauthenticated access to /forecast/sales (expecting 401)...")
    res_unauth = client.get("/api/v1/forecast/sales")
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    print("      [OK] Unauthenticated access properly rejected with 401.")

    # -------------------------------------------------------------------------
    # TEST 2: Sales Trend Analytics (GET /api/v1/analytics/sales-trend)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing GET /api/v1/analytics/sales-trend...")
    trend_res = client.get("/api/v1/analytics/sales-trend?days=90", headers=headers)
    assert trend_res.status_code == 200, f"Failed: {trend_res.text}"
    trend_data = trend_res.json()

    assert "points" in trend_data
    assert "day_of_week_pattern" in trend_data
    assert "total_revenue" in trend_data
    assert "avg_daily_revenue" in trend_data
    assert "peak_day" in trend_data
    assert len(trend_data["points"]) > 0
    assert len(trend_data["day_of_week_pattern"]) == 7

    sample_point = trend_data["points"][0]
    assert "ma_7" in sample_point
    assert "ma_30" in sample_point
    print(f"      [OK] 90-day trend points: {len(trend_data['points'])} | Peak Day: {trend_data['peak_day']} (INR {trend_data['peak_day_revenue']:,.2f})")
    print(f"      [OK] Day-of-week patterns: {len(trend_data['day_of_week_pattern'])} days evaluated.")

    # -------------------------------------------------------------------------
    # TEST 3: Demand Analytics (GET /api/v1/analytics/demand)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Testing GET /api/v1/analytics/demand...")
    demand_res = client.get("/api/v1/analytics/demand", headers=headers)
    assert demand_res.status_code == 200, f"Failed: {demand_res.text}"
    demand_data = demand_res.json()

    assert "categories" in demand_data
    assert "total_units_sold" in demand_data
    assert "total_revenue" in demand_data
    assert len(demand_data["categories"]) > 0
    print(f"      [OK] Categories analyzed: {len(demand_data['categories'])} | Top Category: {demand_data['top_category_name']} | Units: {demand_data['total_units_sold']}")

    # -------------------------------------------------------------------------
    # TEST 4: Product Performance & Pareto 80/20 (GET /api/v1/analytics/product-performance)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Testing GET /api/v1/analytics/product-performance...")
    prod_res = client.get("/api/v1/analytics/product-performance?limit=50", headers=headers)
    assert prod_res.status_code == 200, f"Failed: {prod_res.text}"
    prod_data = prod_res.json()

    assert "products" in prod_data
    assert "pareto_summary" in prod_data
    assert prod_data["total_skus_analyzed"] > 0
    print(f"      [OK] SKUs analyzed: {prod_data['total_skus_analyzed']} | Pareto Distribution: {prod_data['pareto_summary']}")

    # -------------------------------------------------------------------------
    # TEST 5: Features Explanation (GET /api/v1/forecast/features)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Testing GET /api/v1/forecast/features...")
    feat_res = client.get("/api/v1/forecast/features", headers=headers)
    assert feat_res.status_code == 200, f"Failed: {feat_res.text}"
    features = feat_res.json()
    assert "day_of_week" in features
    assert "lag_7" in features
    assert "rolling_mean_7" in features
    print(f"      [OK] {len(features)} ML features explained and documented.")

    # -------------------------------------------------------------------------
    # TEST 6: 7-Day Sales Forecast (GET /api/v1/forecast/sales?days=7)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Testing GET /api/v1/forecast/sales?days=7...")
    fc7_res = client.get("/api/v1/forecast/sales?days=7", headers=headers)
    assert fc7_res.status_code == 200, f"Failed: {fc7_res.text}"
    fc7_data = fc7_res.json()

    assert fc7_data["horizon_days"] == 7
    assert "evaluation_metrics" in fc7_data
    metrics = fc7_data["evaluation_metrics"]
    assert "mae" in metrics
    assert "rmse" in metrics
    assert "mape" in metrics
    assert "wape" in metrics
    assert "r2" in metrics

    # Check forecast data points
    forecast_points = [p for p in fc7_data["data"] if p["is_forecast"]]
    assert len(forecast_points) == 7, f"Expected 7 forecast points, got {len(forecast_points)}"
    for p in forecast_points:
        assert p["forecast_sales"] is not None
        assert p["lower_bound"] is not None
        assert p["upper_bound"] is not None
        assert p["lower_bound"] <= p["forecast_sales"] <= p["upper_bound"] + 1.0

    print(f"      [OK] 7-Day Forecast Generated! Model: {fc7_data['model_name']}")
    print(f"      [OK] Evaluation: MAE={metrics['mae']:,.2f}, RMSE={metrics['rmse']:,.2f}, MAPE={metrics['mape']}%, WAPE={metrics['wape']}%")
    print(f"      [OK] Total 7-day projected revenue: INR {fc7_data['total_forecast_revenue']:,.2f}")

    # -------------------------------------------------------------------------
    # TEST 7: 30-Day Sales Forecast (GET /api/v1/forecast/sales?days=30)
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Testing GET /api/v1/forecast/sales?days=30 (Cached Fast Response)...")
    fc30_res = client.get("/api/v1/forecast/sales?days=30", headers=headers)
    assert fc30_res.status_code == 200, f"Failed: {fc30_res.text}"
    fc30_data = fc30_res.json()

    assert fc30_data["horizon_days"] == 30
    forecast_points_30 = [p for p in fc30_data["data"] if p["is_forecast"]]
    assert len(forecast_points_30) == 30, f"Expected 30 forecast points, got {len(forecast_points_30)}"
    print(f"      [OK] 30-Day Forecast Generated! Total 30-day projected revenue: INR {fc30_data['total_forecast_revenue']:,.2f}")
    print(f"      [OK] Average daily projected sales: INR {fc30_data['avg_daily_forecast']:,.2f}")

    print("\n" + "=" * 70)
    print("PHASE 8 ML ANALYTICS & FORECASTING: ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_phase8_ml_and_forecasting()
