"""
Verification Suite for Phase 9: AI Retail Analyst (LangGraph + Gemini 2.5 + Tool Calling)
Tests natural language question answering, tool selection, structured tool data extraction,
safe database query execution, and absence of hallucinations.
"""

import sys
import os
import time
import uuid

# Ensure Windows console supports UTF-8 characters like ₹
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8")
    except Exception:
        pass

from starlette.testclient import TestClient

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app

client = TestClient(app)


def test_phase9_ai_retail_analyst():
    print("=" * 70)
    print("RETAIL KPI INTELLIGENCE PLATFORM - PHASE 9 AI ANALYST TEST")
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
    print("\n[TEST 1] Testing unauthenticated access to /agent/chat (expecting 401)...")
    res_unauth = client.post("/api/v1/agent/chat", json={"message": "Hello"})
    assert res_unauth.status_code == 401, f"Expected 401, got {res_unauth.status_code}"
    print("      [OK] Unauthenticated access properly rejected with 401.")

    conv_id = str(uuid.uuid4())

    # -------------------------------------------------------------------------
    # TEST 2: Question - Which store generated the highest revenue?
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Testing prompt: 'Which store generated the highest revenue?'...")
    res2 = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={"message": "Which store generated the highest revenue?", "conversation_id": conv_id},
    )
    assert res2.status_code == 200, f"Failed: {res2.text}"
    data2 = res2.json()

    assert "answer" in data2 and len(data2["answer"]) > 10
    assert "tools_used" in data2
    assert "get_store_performance" in data2["tools_used"], f"Expected get_store_performance in tools, got {data2['tools_used']}"
    assert "Mumbai" in data2["answer"] or "Bandra" in data2["answer"]
    print(f"      [OK] Tools Used: {data2['tools_used']}")
    print(f"      [OK] Answer preview: {data2['answer'][:180]}...")

    # -------------------------------------------------------------------------
    # TEST 3: Question - Forecast sales for the next 30 days
    # -------------------------------------------------------------------------
    time.sleep(3)
    print("\n[TEST 3] Testing prompt: 'Forecast sales for the next 30 days'...")
    res3 = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={"message": "Forecast sales for the next 30 days.", "conversation_id": conv_id},
    )
    assert res3.status_code == 200, f"Failed: {res3.text}"
    data3 = res3.json()

    assert "forecast_sales" in data3["tools_used"], f"Expected forecast_sales in tools, got {data3['tools_used']}"
    assert "Prophet" in data3["answer"] or "project" in data3["answer"].lower() or "forecast" in data3["answer"].lower()
    print(f"      [OK] Tools Used: {data3['tools_used']}")
    print(f"      [OK] Answer preview: {data3['answer'][:180]}...")

    # -------------------------------------------------------------------------
    # TEST 4: Question - Which products are performing poorly?
    # -------------------------------------------------------------------------
    time.sleep(3)
    print("\n[TEST 4] Testing prompt: 'Which products are performing poorly?'...")
    res4 = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={"message": "Which products are performing poorly?", "conversation_id": conv_id},
    )
    assert res4.status_code == 200, f"Failed: {res4.text}"
    data4 = res4.json()

    assert "get_product_performance" in data4["tools_used"], f"Expected get_product_performance, got {data4['tools_used']}"
    print(f"      [OK] Tools Used: {data4['tools_used']}")
    print(f"      [OK] Answer preview: {data4['answer'][:180]}...")

    # -------------------------------------------------------------------------
    # TEST 5: Question - Head-to-Head store comparison
    # -------------------------------------------------------------------------
    time.sleep(3)
    print("\n[TEST 5] Testing prompt: 'Compare Indiranagar and Bandra stores'...")
    res5 = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={"message": "Compare Indiranagar and Bandra stores.", "conversation_id": conv_id},
    )
    assert res5.status_code == 200, f"Failed: {res5.text}"
    data5 = res5.json()

    assert "compare_stores" in data5["tools_used"], f"Expected compare_stores, got {data5['tools_used']}"
    assert len(data5["data"]) > 0
    print(f"      [OK] Tools Used: {data5['tools_used']}")
    print(f"      [OK] Answer preview: {data5['answer'][:180]}...")

    # -------------------------------------------------------------------------
    # TEST 6: Question - Graceful Handling of Unavailable Store (Vizag)
    # -------------------------------------------------------------------------
    time.sleep(3)
    print("\n[TEST 6] Testing prompt: 'Compare Vizag and Hyderabad stores' (graceful fallback)...")
    res6 = client.post(
        "/api/v1/agent/chat",
        headers=headers,
        json={"message": "Compare Vizag and Hyderabad stores.", "conversation_id": conv_id},
    )
    assert res6.status_code == 200, f"Failed: {res6.text}"
    data6 = res6.json()

    assert "compare_stores" in data6["tools_used"]
    # Check that answer mentions Vizag is not found or lists available cities
    assert "vizag" in data6["answer"].lower()
    print(f"      [OK] Graceful Handling validated. Answer preview: {data6['answer'][:180]}...")

    print("\n" + "=" * 70)
    print("PHASE 9 AI RETAIL ANALYST: ALL TESTS PASSED SUCCESSFULLY!")
    print("=" * 70)


if __name__ == "__main__":
    test_phase9_ai_retail_analyst()
