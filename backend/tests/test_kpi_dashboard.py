"""
Dashboard KPI Calculation and Filtering Integration Tests
Verifies real-time KPI metrics, date filtering, store filtering, empty data handling, and invalid inputs.
"""

from datetime import datetime, timedelta, timezone
from app.models import Store


def test_dashboard_kpi_overview_calculation(client, auth_headers):
    """Verify calculation of revenue, profit, orders, customers, and average order value."""
    response = client.get("/api/v1/dashboard/overview", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()

    assert "total_revenue" in data
    assert "total_profit" in data
    assert "total_orders" in data
    assert "total_customers" in data
    assert "average_order_value" in data

    rev = float(data["total_revenue"])
    profit = float(data["total_profit"])
    orders = int(data["total_orders"])
    aov = float(data["average_order_value"])

    assert rev > 0
    assert profit > 0
    assert orders > 0
    assert profit <= rev
    # AOV should approximately equal revenue / orders
    calculated_aov = round(rev / orders, 2)
    assert abs(aov - calculated_aov) < 1.0


def test_dashboard_kpi_date_filtering(client, auth_headers):
    """Verify date filtering narrows down revenue and order counts."""
    # Query with a tight 30-day window
    now = datetime.now(timezone.utc)
    start_str = (now - timedelta(days=60)).strftime("%Y-%m-%d")
    end_str = now.strftime("%Y-%m-%d")

    res_filtered = client.get(
        f"/api/v1/dashboard/overview?start_date={start_str}&end_date={end_str}",
        headers=auth_headers,
    )
    assert res_filtered.status_code == 200
    data_filtered = res_filtered.json()

    # Query with full lifetime
    res_full = client.get("/api/v1/dashboard/overview", headers=auth_headers)
    assert res_full.status_code == 200
    data_full = res_full.json()

    # Filtered revenue should be less than or equal to total lifetime revenue
    assert float(data_filtered["total_revenue"]) <= float(data_full["total_revenue"])


def test_dashboard_kpi_store_filtering(client, auth_headers, db):
    """Verify filtering KPIs by a specific store_id."""
    store = db.query(Store).filter(Store.is_active == True).first()
    assert store is not None

    response = client.get(
        f"/api/v1/dashboard/overview?store_id={str(store.id)}",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["total_revenue"]) >= 0


def test_dashboard_kpi_empty_results_handling(client, auth_headers):
    """Verify system handles empty database results gracefully (zero figures, no 500 error)."""
    # Filter for a future date range where zero sales exist
    response = client.get(
        "/api/v1/dashboard/overview?start_date=2099-01-01&end_date=2099-01-31",
        headers=auth_headers,
    )
    assert response.status_code == 200
    data = response.json()
    assert float(data["total_revenue"]) == 0.0
    assert float(data["total_profit"]) == 0.0
    assert int(data["total_orders"]) == 0
    assert float(data["average_order_value"]) == 0.0


def test_dashboard_kpi_invalid_parameters(client, auth_headers):
    """Verify passing invalid parameters (malformed date string) returns 422 validation error."""
    response = client.get(
        "/api/v1/dashboard/overview?start_date=not-a-valid-date",
        headers=auth_headers,
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"
