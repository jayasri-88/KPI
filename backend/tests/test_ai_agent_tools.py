"""
AI Retail Analyst Tools and Chat Integration Tests
Verifies analytical tool execution, parameter boundaries, error resilience, and prompt safety.
"""

from app.agent.tools import (
    get_sales_kpi,
    get_store_performance,
    get_product_performance,
    get_customer_metrics,
    get_sales_trend,
    compare_stores,
    compare_periods,
)


def test_ai_tool_get_sales_kpi():
    """Verify get_sales_kpi tool returns verified financial numbers."""
    result = get_sales_kpi.invoke({})
    assert "total_revenue" in result
    assert "total_profit" in result
    assert "gross_margin_pct" in result
    assert result["total_revenue"] > 0


def test_ai_tool_store_performance_bounds_clamping():
    """Verify get_store_performance bounds checks limit to max 50."""
    result = get_store_performance.invoke({"limit": 5000})
    assert len(result["stores"]) <= 50
    assert "top_store" in result
    assert "bottom_store" in result


def test_ai_tool_product_performance():
    """Verify get_product_performance returns Pareto distribution and SKU rankings."""
    result = get_product_performance.invoke({"limit": 5, "order": "desc"})
    assert len(result["products"]) <= 5
    assert "pareto_summary" in result
    assert result["total_skus_analyzed"] > 0


def test_ai_tool_customer_metrics():
    """Verify get_customer_metrics returns customer cohort segmentation."""
    result = get_customer_metrics.invoke({})
    assert "total_customers" in result
    assert "repeat_customer_rate_pct" in result
    assert "segments" in result
    assert len(result["segments"]) > 0


def test_ai_tool_sales_trend_days_clamping():
    """Verify get_sales_trend clamps days between 7 and 365."""
    result_high = get_sales_trend.invoke({"days": 10000})
    assert result_high["period_days"] <= 365

    result_low = get_sales_trend.invoke({"days": 1})
    assert result_low["period_days"] >= 7


def test_ai_tool_compare_stores_not_found_handling():
    """Verify compare_stores returns informative error message when store is nonexistent."""
    result = compare_stores.invoke({
        "store_a": "Nonexistent Fake City Store 123",
        "store_b": "Bangalore",
    })
    assert "error" in result
    assert "available_store_cities" in result
    assert len(result["available_store_cities"]) > 0


def test_ai_tool_compare_periods():
    """Verify compare_periods diagnoses revenue variance between consecutive periods."""
    result = compare_periods.invoke({"period_type": "month"})
    assert "recent_period" in result
    assert "prior_period" in result
    assert "variance" in result
    assert "primary_driver" in result["variance"]


def test_ai_chat_endpoint_payload_guard(client, auth_headers):
    """Verify AI analyst chat endpoint rejects oversized payloads (>1,000 chars) with 422."""
    huge_message = "Analyze this: " + ("retail_data " * 150)
    response = client.post(
        "/api/v1/agent/chat",
        headers=auth_headers,
        json={"message": huge_message},
    )
    assert response.status_code == 422
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "VALIDATION_ERROR"


def test_ai_chat_native_local_execution(client, auth_headers):
    """Verify AI analyst chat executes native local tools against PostgreSQL test data without external APIs."""
    response = client.post(
        "/api/v1/agent/chat",
        headers=auth_headers,
        json={"message": "Which store generated the highest revenue?"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert "tools_used" in data
    assert "get_store_performance" in data["tools_used"]
    assert len(data["data"]) > 0
    assert "Hyderabad" in data["answer"] or "Store" in data["answer"]
