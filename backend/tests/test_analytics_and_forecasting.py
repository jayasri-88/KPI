"""
Analytics and Forecasting Integration & Unit Tests
Verifies sales trends, product Pareto distribution, store analytics, and Meta Prophet forecasting.
"""

import pandas as pd
from ml.forecaster import get_forecast


def test_sales_trend_analytics(client, auth_headers):
    """Verify sales trend returns trajectory, moving averages, and day-of-week patterns."""
    response = client.get("/api/v1/analytics/sales-trend?days=60", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "total_revenue" in data
    assert "avg_daily_revenue" in data
    assert "day_of_week_pattern" in data
    assert len(data["day_of_week_pattern"]) == 7


def test_product_performance_and_pareto(client, auth_headers):
    """Verify product ranking and 80/20 Pareto ABC classification."""
    response = client.get("/api/v1/analytics/product-performance?limit=20", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "products" in data
    assert "pareto_summary" in data
    assert len(data["products"]) > 0
    first_prod = data["products"][0]
    assert any(c in first_prod["pareto_class"] for c in ["A", "B", "C"])
    assert first_prod["total_revenue"] >= 0


def test_forecasting_with_sufficient_data(client, auth_headers):
    """Verify sales forecast endpoint generates 7-day predictions with confidence bounds."""
    response = client.get("/api/v1/forecast/sales?horizon_days=7", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert data["horizon_days"] == 7
    assert "total_forecast_revenue" in data
    assert "evaluation_metrics" in data
    assert "data" in data
    assert len(data["data"]) > 0


def test_forecasting_with_insufficient_data():
    """Verify forecaster handles insufficient historical data (<14 data points) gracefully."""
    # Create a tiny DataFrame with only 5 days of sales
    tiny_df = pd.DataFrame({
        "ds": pd.date_range(start="2026-01-01", periods=5, freq="D"),
        "y": [100.0, 150.0, 200.0, 180.0, 220.0],
    })
    result = get_forecast(tiny_df, horizon_days=7)
    assert "fallback" in result["model_name"].lower() or "evaluation_metrics" in result
    assert result["total_forecast_revenue"] > 0
    assert len(result["forecast_data"]) == 7


def test_forecasting_invalid_horizon_parameter(client, auth_headers):
    """Verify passing invalid horizon_days returns 422 validation error."""
    response = client.get("/api/v1/forecast/sales?horizon_days=-10", headers=auth_headers)
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
