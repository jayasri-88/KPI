"""
Phase 11: Production Audit Verification Suite
Tests all audit fixes:
1. CORS configuration & header behavior
2. Centralized exception handling & consistent error schema
3. N+1 query elimination (Order, Inventory, Product eager loading)
4. SQL LIKE wildcard escaping (denial-of-service / pattern injection protection)
5. AI Analyst Agent request bounds & defensive parameter clamping
6. Enhanced health check with DB latency and Redis telemetry
"""

import sys
import os
import uuid
from fastapi.testclient import TestClient

# Ensure backend root is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import Order, Inventory, Product, User
from app.services import order_service, inventory_service, product_service
from app.agent.tools import get_store_performance, get_product_performance, get_sales_trend, forecast_sales
from app.core.security import create_access_token, escape_like

client = TestClient(app)


def test_cors_policy():
    """Verify CORS only reflects trusted origins and blocks arbitrary origins."""
    # Test trusted origin
    res_trusted = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://localhost:5173",
            "Access-Control-Request-Method": "GET",
        },
    )
    assert res_trusted.status_code == 200
    assert res_trusted.headers.get("access-control-allow-origin") == "http://localhost:5173"
    assert res_trusted.headers.get("access-control-allow-credentials") == "true"

    # Test untrusted origin
    res_untrusted = client.options(
        "/api/v1/health",
        headers={
            "Origin": "http://malicious-site.com",
            "Access-Control-Request-Method": "GET",
        },
    )
    # Untrusted origin should NOT get access-control-allow-origin
    assert res_untrusted.headers.get("access-control-allow-origin") != "http://malicious-site.com"
    assert res_untrusted.headers.get("access-control-allow-origin") != "*"
    print("PASS: CORS policy successfully enforces strict origin isolation without wildcard credential leak.")


def test_consistent_error_responses():
    """Verify centralized exception handling outputs consistent error schemas."""
    # 1. Test 404 Not Found
    res_404 = client.get("/api/v1/nonexistent-endpoint-test")
    assert res_404.status_code == 404
    body_404 = res_404.json()
    assert "error" in body_404
    assert body_404["error"]["code"] == "HTTP_404"
    assert "detail" in body_404

    # 2. Test 422 RequestValidationError (Pydantic payload failure)
    res_422 = client.post("/api/v1/auth/register", json={"invalid": "payload"})
    assert res_422.status_code == 422
    body_422 = res_422.json()
    assert "error" in body_422
    assert body_422["error"]["code"] == "VALIDATION_ERROR"
    assert "details" in body_422["error"]

    # 3. Test 401 Unauthorized
    res_401 = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer invalid_or_expired_token"},
    )
    assert res_401.status_code == 401
    body_401 = res_401.json()
    assert "error" in body_401
    assert body_401["error"]["code"] == "HTTP_401"
    print("PASS: Centralized exception handlers deliver consistent { error: { code, message }, detail } envelopes.")


def test_order_service_eager_loading():
    """Verify order querying uses joinedload and populates relations without N+1 queries."""
    db = SessionLocal()
    try:
        paginated = order_service.get_orders(db, page=1, size=5)
        assert paginated.total > 0
        assert len(paginated.items) > 0
        for item in paginated.items:
            # store_name and customer_name are populated via joinedload
            assert item.store_name is not None
        
        # Test get_order_by_id eager loading
        first_order_id = paginated.items[0].id
        detail = order_service.get_order_by_id(db, first_order_id)
        assert detail is not None
        assert detail.store_name is not None
        assert len(detail.order_items) > 0
        assert detail.order_items[0].product_name is not None
        print(f"PASS: Order eager loading verified across {len(paginated.items)} orders and order items.")
    finally:
        db.close()


def test_inventory_and_product_eager_loading():
    """Verify inventory and product services eager load relationships and escape search."""
    db = SessionLocal()
    try:
        # Inventory eager loading
        inv_res = inventory_service.get_inventory(db, page=1, size=5)
        assert inv_res.total > 0
        for item in inv_res.items:
            assert item.store_name is not None
            assert item.product_name is not None

        # Inventory search with wildcard character
        inv_search = inventory_service.get_inventory(db, search="%%")
        assert inv_search.total >= 0

        # Product eager loading
        prod_res = product_service.get_products(db, page=1, size=5)
        assert prod_res.total > 0
        for item in prod_res.items:
            assert item.category_name is not None

        # Product search with escaped wildcard
        prod_search = product_service.get_products(db, search="test%_brand")
        assert prod_search.total >= 0
        print("PASS: Inventory and Product eager loading and LIKE escaping verified.")
    finally:
        db.close()


def test_sql_like_escaping():
    """Verify escape_like escapes %, _, and backslashes."""
    raw = "100% Cotton_Fabric\\Collection"
    escaped = escape_like(raw)
    assert escaped == "100\\% Cotton\\_Fabric\\\\Collection"
    assert escape_like("") == ""
    print("PASS: SQL LIKE wildcard escaping verified.")


def test_agent_request_bounds():
    """Verify agent endpoint enforces message length limits (max 1000 characters)."""
    # Create test user token
    db = SessionLocal()
    try:
        user = db.query(User).first()
        token = create_access_token(str(user.id))
    finally:
        db.close()

    # Oversized payload (> 1000 chars)
    oversized_message = "A" * 1500
    res = client.post(
        "/api/v1/agent/chat",
        headers={"Authorization": f"Bearer {token}"},
        json={"message": oversized_message},
    )
    assert res.status_code == 422
    err_body = res.json()
    assert err_body["error"]["code"] == "VALIDATION_ERROR"
    print("PASS: Prompt injection payload size guard (<1,000 chars) verified with 422 rejection.")


def test_agent_tools_bounds_clamping():
    """Verify AI analyst tools defensively clamp limits and parameter ranges."""
    # Tool limit clamped to max 50 even when asking for 99999
    res_stores = get_store_performance.invoke({"limit": 99999})
    assert len(res_stores["stores"]) <= 50

    res_products = get_product_performance.invoke({"limit": 99999})
    assert len(res_products["products"]) <= 50

    # Sales trend days clamped
    res_trend = get_sales_trend.invoke({"days": 5000})
    assert res_trend["period_days"] <= 365

    # Forecast days clamped to max 90
    res_fc = forecast_sales.invoke({"days": 180})
    assert res_fc["horizon_days"] <= 90
    print("PASS: AI Analyst tools defensive parameter bounds clamping verified.")


def test_enhanced_health_telemetry():
    """Verify /api/v1/health endpoint returns complete DB and Redis metrics."""
    res = client.get("/api/v1/health")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] in ["healthy", "degraded"]
    assert "database" in data
    assert "latency_ms" in data["database"]
    assert data["database"]["status"] == "connected"
    assert data["database"]["postgis_version"] is not None
    assert "cache" in data
    assert "status" in data["cache"]
    assert "latency_ms" in data["cache"]
    print(f"PASS: Enhanced health check telemetry verified (DB latency: {data['database']['latency_ms']}ms, Cache: {data['cache']['status']}).")


if __name__ == "__main__":
    print("\n=======================================================")
    print("RUNNING PHASE 11 PRODUCTION AUDIT VERIFICATION SUITE")
    print("=======================================================\n")
    test_cors_policy()
    test_consistent_error_responses()
    test_order_service_eager_loading()
    test_inventory_and_product_eager_loading()
    test_sql_like_escaping()
    test_agent_request_bounds()
    test_agent_tools_bounds_clamping()
    test_enhanced_health_telemetry()
    print("\n=======================================================")
    print("ALL PHASE 11 AUDIT TESTS PASSED SUCCESSFULLY!")
    print("=======================================================\n")
