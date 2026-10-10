"""Phase 1 Verification Script for Retail KPI Intelligence Platform."""
import sys
from fastapi.testclient import TestClient

try:
    from app.main import app
    client = TestClient(app)

    print("[1/4] Testing Root Endpoint (GET /)...")
    r1 = client.get("/")
    assert r1.status_code == 200, f"Expected 200, got {r1.status_code}"
    print("      Status: 200 OK | Response:", r1.json())

    print("[2/4] Testing Versioned Health Endpoint (GET /api/v1/health)...")
    r2 = client.get("/api/v1/health")
    assert r2.status_code == 200, f"Expected 200, got {r2.status_code}"
    print("      Status: 200 OK | Response:", r2.json())

    print("[3/4] Testing Convenience Health Endpoint (GET /health)...")
    r3 = client.get("/health")
    assert r3.status_code == 200, f"Expected 200, got {r3.status_code}"
    print("      Status: 200 OK | Status: Healthy")

    print("[4/4] Testing Swagger UI Documentation (GET /docs)...")
    r4 = client.get("/docs")
    assert r4.status_code == 200, f"Expected 200, got {r4.status_code}"
    print("      Status: 200 OK | Swagger UI accessible at /docs")

    print("\n>>> ALL PHASE 1 BACKEND VERIFICATION CHECKS PASSED SUCCESSFULLY! <<<")
except Exception as e:
    print(f"\n[ERROR] Phase 1 check failed: {e}", file=sys.stderr)
    sys.exit(1)
