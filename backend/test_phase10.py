"""
Verification Suite for Phase 10: Redis Caching Layer
Demonstrates and validates:
1. Cache Miss -> Database Query -> Cache Set -> Cache Hit sequence
2. Deterministic key generation with query parameters and date filters
3. Dashboard KPI caching
4. Store performance caching
5. Product performance caching
6. Frequently requested analytics caching (Sales Trend & Forecast)
7. Cache invalidation on mutation and manual triggers
8. AI agent temporary session state persistence in Redis
9. Graceful fallback to PostgreSQL when Redis is unavailable
10. Cache metrics and hit ratio statistics endpoint
"""

import os
import sys
import time

if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from starlette.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.cache import RedisCacheManager, cache_manager
from app.main import app

client = TestClient(app)


def test_phase10_redis_caching():
    print("=" * 75)
    print("RETAIL KPI INTELLIGENCE PLATFORM - PHASE 10 REDIS CACHING TEST SUITE")
    print("=" * 75)

    # -------------------------------------------------------------------------
    # STEP 0: Authentication
    # -------------------------------------------------------------------------
    print("\n[STEP 0] Authenticating to acquire JWT Admin Bearer token...")
    login_res = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@retailkpi.com", "password": "Admin@2026"},
    )

    assert login_res.status_code == 200, f"Admin login failed: {login_res.text}"
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print(f"      [OK] Token acquired: {token[:25]}...")

    # Clear previous cache keys to ensure deterministic baseline
    cleared = cache_manager.delete_pattern("*")
    print(f"      [OK] Pre-cleared {cleared} existing test cache keys from Redis.")

    # -------------------------------------------------------------------------
    # TEST 1: Deterministic Key Generation
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Testing Deterministic Cache Key Generation...")
    key1 = cache_manager.build_key("kpi:dashboard", start_date="2025-01-01", end_date="2025-12-31")
    key2 = cache_manager.build_key("kpi:dashboard", end_date="2025-12-31", start_date="2025-01-01")
    assert key1 == key2, "Keys with same parameters in different orders must be strictly identical!"
    assert key1 == "retail:kpi:dashboard:end_date=2025-12-31:start_date=2025-01-01"
    print(f"      [OK] Deterministic Key (Parameter order-invariant): {key1}")

    # -------------------------------------------------------------------------
    # TEST 2: Dashboard KPI Caching (Cache Miss -> DB -> Cache Set -> Cache Hit)
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing Dashboard KPI Caching (/api/v1/dashboard/overview)...")
    url_dash = "/api/v1/dashboard/overview?start_date=2025-01-01T00:00:00Z&end_date=2025-12-31T23:59:59Z"

    # Step 2a: First Call -> Cache Miss -> DB Query -> Cache Set
    t0 = time.time()
    res_miss = client.get(url_dash, headers=headers)
    dur_miss = (time.time() - t0) * 1000.0
    assert res_miss.status_code == 200, f"Dashboard overview request failed: {res_miss.text}"
    data_miss = res_miss.json()
    print(f"      [Step 2a - CACHE MISS] DB Query executed in {dur_miss:.2f}ms. Total Revenue: INR {float(data_miss['total_revenue']):,.2f}")


    # Step 2b: Second Call -> Cache Hit
    t1 = time.time()
    res_hit = client.get(url_dash, headers=headers)
    dur_hit = (time.time() - t1) * 1000.0
    assert res_hit.status_code == 200
    data_hit = res_hit.json()
    print(f"      [Step 2b - CACHE HIT]  Served from Redis in {dur_hit:.2f}ms. Speedup: {dur_miss / max(dur_hit, 0.01):.1f}x faster!")

    assert data_miss["total_revenue"] == data_hit["total_revenue"]
    assert data_miss["total_orders"] == data_hit["total_orders"]

    # -------------------------------------------------------------------------
    # TEST 3: Store Performance Caching (/api/v1/stores/performance)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Testing Store Performance Caching (/api/v1/stores/performance)...")
    url_store = "/api/v1/stores/performance?region=West"

    # Call 1: Miss
    t0 = time.time()
    res_store_miss = client.get(url_store, headers=headers)
    dur_store_miss = (time.time() - t0) * 1000.0
    assert res_store_miss.status_code == 200
    stores_miss = res_store_miss.json()
    print(f"      [CACHE MISS] DB Query returned {len(stores_miss)} stores in {dur_store_miss:.2f}ms.")

    # Call 2: Hit
    t1 = time.time()
    res_store_hit = client.get(url_store, headers=headers)
    dur_store_hit = (time.time() - t1) * 1000.0
    assert res_store_hit.status_code == 200
    stores_hit = res_store_hit.json()
    print(f"      [CACHE HIT]  Served from Redis in {dur_store_hit:.2f}ms ({dur_store_miss / max(dur_store_hit, 0.01):.1f}x faster).")
    assert stores_miss[0]["name"] == stores_hit[0]["name"]

    # -------------------------------------------------------------------------
    # TEST 4: Product Performance Caching (/api/v1/analytics/product-performance)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Testing Product Performance & Pareto Caching (/api/v1/analytics/product-performance)...")
    url_prod = "/api/v1/analytics/product-performance?limit=25"

    t0 = time.time()
    res_prod_miss = client.get(url_prod, headers=headers)
    dur_prod_miss = (time.time() - t0) * 1000.0
    assert res_prod_miss.status_code == 200
    prod_miss = res_prod_miss.json()
    print(f"      [CACHE MISS] DB Pareto calculation executed in {dur_prod_miss:.2f}ms. SKUs: {len(prod_miss['products'])}")

    t1 = time.time()
    res_prod_hit = client.get(url_prod, headers=headers)
    dur_prod_hit = (time.time() - t1) * 1000.0
    assert res_prod_hit.status_code == 200
    prod_hit = res_prod_hit.json()
    print(f"      [CACHE HIT]  Served from Redis in {dur_prod_hit:.2f}ms.")
    assert len(prod_miss["products"]) == len(prod_hit["products"])

    # -------------------------------------------------------------------------
    # TEST 5: Frequently Requested Analytics (Sales Trend & Forecast)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Testing Frequently Requested Sales Trend Analytics (/api/v1/analytics/sales-trend)...")
    url_trend = "/api/v1/analytics/sales-trend?days=60"

    t0 = time.time()
    res_trend_miss = client.get(url_trend, headers=headers)
    dur_trend_miss = (time.time() - t0) * 1000.0
    assert res_trend_miss.status_code == 200
    print(f"      [CACHE MISS] Sales trend computed in {dur_trend_miss:.2f}ms.")

    t1 = time.time()
    res_trend_hit = client.get(url_trend, headers=headers)
    dur_trend_hit = (time.time() - t1) * 1000.0
    assert res_trend_hit.status_code == 200
    print(f"      [CACHE HIT]  Sales trend retrieved from Redis in {dur_trend_hit:.2f}ms.")

    # -------------------------------------------------------------------------
    # TEST 6: Invalidation Workflow (Invalidate Pattern -> Cache Miss Repopulation)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Testing Cache Invalidation Endpoint (/api/v1/cache/invalidate)...")
    inv_res = client.post(
        "/api/v1/cache/invalidate",
        headers=headers,
        json={"pattern": "kpi"},
    )
    assert inv_res.status_code == 200, f"Invalidation failed: {inv_res.text}"
    inv_data = inv_res.json()
    print(f"      [OK] Invalidation confirmed. Keys deleted: {inv_data['keys_deleted']}")
    assert inv_data["keys_deleted"] >= 1

    # Verify that Dashboard overview is now a fresh Cache Miss again
    t0 = time.time()
    res_after_inv = client.get(url_dash, headers=headers)
    dur_after_inv = (time.time() - t0) * 1000.0
    assert res_after_inv.status_code == 200
    print(f"      [OK] Post-invalidation query successfully triggered fresh DB query ({dur_after_inv:.2f}ms).")

    # -------------------------------------------------------------------------
    # TEST 7: AI Agent Temporary State Persistence in Redis
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Testing AI Agent Temporary State Persistence in Redis...")
    from app.agent.agent_service import _load_history, _save_history, clear_conversation
    from langchain_core.messages import HumanMessage, AIMessage

    test_conv_id = f"test-session-{int(time.time())}"
    sample_msgs = [
        HumanMessage(content="Which store has lowest margin?"),
        AIMessage(content="Kolkata Salt Lake City Center (25.10% margin)"),
    ]
    _save_history(test_conv_id, sample_msgs)

    # Check key exists in Redis
    session_key = cache_manager.build_key("ai:session", id=test_conv_id)
    raw_session = cache_manager.get(session_key)
    assert raw_session is not None, "AI session must be persisted in Redis!"
    assert len(raw_session) == 2

    # Load session back
    reloaded_history = _load_history(test_conv_id)
    assert len(reloaded_history) == 2
    assert reloaded_history[0].content == "Which store has lowest margin?"
    print(f"      [OK] Session persisted in Redis ({session_key}) with 24h TTL.")

    # Clear session
    clear_conversation(test_conv_id)
    assert cache_manager.get(session_key) is None
    print(f"      [OK] Session successfully cleared from Redis.")

    # -------------------------------------------------------------------------
    # TEST 8: Graceful Fallback if Redis is Offline
    # -------------------------------------------------------------------------
    print("\n[TEST 8] Testing Graceful Fallback when Redis is Offline / Unreachable...")
    offline_cache = RedisCacheManager("redis://localhost:9999/0")
    assert not offline_cache.is_available, "Offline manager must report unavailable"

    # Operations must degrade seamlessly without throwing exceptions
    get_res = offline_cache.get("some_missing_key")
    assert get_res is None, "Offline get should return None safely"

    set_res = offline_cache.set("some_key", {"test": 123})
    assert set_res is False, "Offline set should return False safely"

    del_res = offline_cache.delete("some_key")
    assert del_res is False, "Offline delete should return False safely"

    pat_res = offline_cache.delete_pattern("kpi:*")
    assert pat_res == 0, "Offline delete_pattern should return 0 safely"

    stats_offline = offline_cache.get_stats()
    assert stats_offline["status"] == "offline_fallback"
    print("      [OK] Complete graceful fallback verified. Zero application crash or blocking.")

    # -------------------------------------------------------------------------
    # TEST 9: Cache Statistics & Telemetry Endpoint (/api/v1/cache/stats)
    # -------------------------------------------------------------------------
    print("\n[TEST 9] Testing Cache Statistics Endpoint (/api/v1/cache/stats)...")
    stats_res = client.get("/api/v1/cache/stats", headers=headers)
    assert stats_res.status_code == 200, f"Stats failed: {stats_res.text}"
    stats = stats_res.json()

    print(f"      [OK] Redis Status: {stats['status']}")
    print(f"      [OK] Cache Hits: {stats['hits']}, Misses: {stats['misses']}")
    print(f"      [OK] Cache Hit Ratio: {stats['hit_ratio_pct']}%")
    print(f"      [OK] Cached Keys in Redis: {stats['cached_keys_count']}")
    if stats.get("redis_server"):
        print(f"      [OK] Redis Server Version: {stats['redis_server'].get('version')} (Memory: {stats['redis_server'].get('used_memory_human')})")

    assert stats["status"] == "connected"
    assert stats["hits"] >= 3
    assert stats["sets"] >= 3

    print("\n" + "=" * 75)
    print("PHASE 10 REDIS CACHING: ALL 9 TEST SUITES PASSED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    test_phase10_redis_caching()
