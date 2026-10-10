"""
Verification Suite for Phase 7: Geographic Retail Analytics
Tests PostGIS spatial queries, distance calculations, radius filtering,
and regional sales aggregations across retail stores.
"""

import sys
import os
from decimal import Decimal
from starlette.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)


def test_phase7_geographic_apis():
    print("=" * 70)
    print("RETAIL KPI INTELLIGENCE PLATFORM - PHASE 7 GEOGRAPHIC ANALYTICS TEST")
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
    print("\n[TEST 1] Testing unauthenticated access to /spatial (expecting 401)...")
    res_unauth = client.get("/api/v1/stores/spatial")
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    print("      [OK] Unauthenticated access properly rejected with 401.")

    # -------------------------------------------------------------------------
    # TEST 2: List all stores with spatial coordinates & financial metrics
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing GET /api/v1/stores/spatial (all stores)...")
    res_all = client.get("/api/v1/stores/spatial", headers=headers)
    assert res_all.status_code == 200, f"Failed: {res_all.text}"
    stores_data = res_all.json()
    assert len(stores_data) == 10, f"Expected 10 stores, got {len(stores_data)}"

    top_store = stores_data[0]
    assert "store_id" in top_store
    assert "latitude" in top_store
    assert "longitude" in top_store
    assert "total_revenue" in top_store
    assert "sales_per_sqft" in top_store
    assert float(top_store["total_revenue"]) > 0
    print(f"      [OK] 10 stores retrieved. Top store: {top_store['name']} | Rev: INR {float(top_store['total_revenue']):,.2f}")

    # -------------------------------------------------------------------------
    # TEST 3: Regional filtering (GET /api/v1/stores/spatial?region=West)
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Testing GET /api/v1/stores/spatial?region=West...")
    res_west = client.get("/api/v1/stores/spatial?region=West", headers=headers)
    assert res_west.status_code == 200, f"Failed: {res_west.text}"
    west_stores = res_west.json()
    assert len(west_stores) == 3, f"Expected 3 West stores, got {len(west_stores)}"
    for s in west_stores:
        assert s["region"].lower() == "west"
        print(f"      - {s['name']} ({s['city']}): INR {float(s['total_revenue']):,.2f}")
    print("      [OK] Regional filter validated.")

    # -------------------------------------------------------------------------
    # TEST 4: PostGIS Distance Calculation from Bengaluru (12.9784, 77.6408)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Testing PostGIS distance calculation from Bengaluru origin...")
    res_dist = client.get("/api/v1/stores/spatial?lat=12.9784&lng=77.6408", headers=headers)
    assert res_dist.status_code == 200, f"Failed: {res_dist.text}"
    dist_stores = res_dist.json()
    assert len(dist_stores) == 10

    # Nearest store should be Bengaluru Indiranagar Flagship with distance ~ 0 km
    nearest = dist_stores[0]
    assert nearest["distance_km"] is not None
    assert nearest["distance_km"] < 1.0, f"Expected nearest store distance < 1km, got {nearest['distance_km']}"
    print(f"      [OK] Nearest store: {nearest['name']} at {nearest['distance_km']} km")

    # Second nearest should be Whitefield (~11.9 km)
    second = dist_stores[1]
    assert second["distance_km"] is not None
    assert 10.0 <= second["distance_km"] <= 15.0, f"Expected Whitefield distance ~11.9km, got {second['distance_km']}"
    print(f"      [OK] 2nd nearest store: {second['name']} at {second['distance_km']} km")

    # -------------------------------------------------------------------------
    # TEST 5: PostGIS Radius Search (ST_DWithin within 50 km)
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Testing PostGIS radius search (ST_DWithin within 50 km of Bengaluru)...")
    res_radius = client.get("/api/v1/stores/spatial?lat=12.9784&lng=77.6408&radius_km=50", headers=headers)
    assert res_radius.status_code == 200, f"Failed: {res_radius.text}"
    radius_stores = res_radius.json()
    assert len(radius_stores) == 2, f"Expected exactly 2 stores within 50km of Bengaluru, got {len(radius_stores)}"
    for s in radius_stores:
        print(f"      - {s['name']} at {s['distance_km']} km")
    print("      [OK] PostGIS ST_DWithin radius filter validated.")

    # -------------------------------------------------------------------------
    # TEST 6: Regional Performance Aggregations (GET /api/v1/stores/geographic/regions)
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Testing GET /api/v1/stores/geographic/regions...")
    res_regions = client.get("/api/v1/stores/geographic/regions", headers=headers)
    assert res_regions.status_code == 200, f"Failed: {res_regions.text}"
    regions_data = res_regions.json()
    assert len(regions_data) == 4, f"Expected 4 macro-regions, got {len(regions_data)}"

    total_stores_aggregated = 0
    total_revenue_aggregated = Decimal("0.00")
    for r in regions_data:
        assert "region" in r
        assert "store_count" in r
        assert "total_revenue" in r
        assert "centroid_lat" in r
        assert "centroid_lng" in r
        assert "top_store_name" in r
        total_stores_aggregated += r["store_count"]
        total_revenue_aggregated += Decimal(str(r["total_revenue"]))
        print(f"      - {r['region']:6} | Stores: {r['store_count']} | Rev: INR {float(r['total_revenue']):,.2f} | Centroid: ({r['centroid_lat']}, {r['centroid_lng']}) | Top: {r['top_store_name']}")

    assert total_stores_aggregated == 10, f"Expected total 10 stores aggregated, got {total_stores_aggregated}"
    assert total_revenue_aggregated > Decimal("20000000.00"), f"Total revenue unexpected: {total_revenue_aggregated}"
    print(f"      [OK] Regional aggregations verified. All 4 regions cover 10 stores and INR {total_revenue_aggregated:,.2f} revenue.")

    print("\n" + "=" * 70)
    print("PHASE 7 BACKEND GEOGRAPHIC ANALYTICS: ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_phase7_geographic_apis()
