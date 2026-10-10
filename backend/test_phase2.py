"""Phase 2 Verification Script: PostgreSQL + PostGIS + SQLAlchemy."""
import sys
from fastapi.testclient import TestClient
from sqlalchemy import text

try:
    print("=" * 60)
    print("RETAIL KPI PLATFORM - PHASE 2 VERIFICATION")
    print("=" * 60)

    # 1. Test SQLAlchemy Engine & Session
    print("\n[1/4] Testing SQLAlchemy Engine & SessionLocal...")
    from app.database import engine, SessionLocal, get_db
    with engine.connect() as conn:
        res = conn.execute(text("SELECT 1;")).scalar()
        assert res == 1, f"Expected 1, got {res}"
    print("      SUCCESS: SQLAlchemy connected to PostgreSQL via engine.")

    # 2. Test PostGIS Extension & Spatial Query
    print("\n[2/4] Testing PostGIS Extension Availability...")
    with engine.connect() as conn:
        postgis_ver = conn.execute(text("SELECT PostGIS_Version();")).scalar()
        assert postgis_ver, "PostGIS Version returned empty"
        print(f"      SUCCESS: PostGIS is enabled! Version: {postgis_ver}")

        # Run spatial function test
        point_wkt = conn.execute(
            text("SELECT ST_AsText(ST_SetSRID(ST_MakePoint(77.5946, 12.9716), 4326));")
        ).scalar()
        print(f"      SUCCESS: Spatial test (ST_MakePoint Bangalore): {point_wkt}")

    # 3. Test FastAPI Dependency Injection (get_db)
    print("\n[3/4] Testing FastAPI Session Management & Dependency Injection...")
    from app.main import app
    client = TestClient(app)

    db_response = client.get("/api/v1/db-check")
    assert db_response.status_code == 200, f"Expected 200, got {db_response.status_code}"
    db_json = db_response.json()
    assert db_json["success"] is True
    print(f"      SUCCESS: /api/v1/db-check returned 200 OK")
    print(f"      Connected Database: {db_json['database_name']}")
    print(f"      Connected User: {db_json['connected_user']}")
    print(f"      Spatial Output: {db_json['spatial_test_geometry']}")

    # 4. Test Health Check Endpoint
    print("\n[4/4] Testing /api/v1/health Live Diagnostics...")
    health_response = client.get("/api/v1/health")
    assert health_response.status_code == 200, f"Expected 200, got {health_response.status_code}"
    health_json = health_response.json()
    assert health_json["status"] == "healthy"
    assert health_json["database"]["status"] == "connected"
    print(f"      SUCCESS: Overall Status: {health_json['status'].upper()}")
    print(f"      Database Engine: {health_json['database']['engine']}")
    print(f"      PostGIS Status: {health_json['services']['postgis'].upper()}")

    print("\n" + "=" * 60)
    print(">>> ALL PHASE 2 POSTGRESQL + POSTGIS CHECKS PASSED! <<<")
    print("=" * 60)

except Exception as e:
    print(f"\n[ERROR] Phase 2 verification failed: {e}", file=sys.stderr)
    sys.exit(1)
