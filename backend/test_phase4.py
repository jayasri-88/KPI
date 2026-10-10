"""
Verification Suite for Phase 4: Authentication + JWT
Tests all REST endpoints, bcrypt password hashing, token validation,
role-based permissions, and protected route dependencies.
"""

import sys
import os
import uuid
from starlette.testclient import TestClient

# Add backend directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.main import app
from app.database import SessionLocal
from app.models import User

client = TestClient(app)


def test_phase4_authentication():
    print("=" * 65)
    print("RETAIL KPI INTELLIGENCE PLATFORM - PHASE 4 AUTHENTICATION SUITE")
    print("=" * 65)

    test_uid = uuid.uuid4().hex[:6]
    test_email = f"test_analyst_{test_uid}@retailkpi.com"
    test_username = f"user_{test_uid}"
    test_password = "SecurePassword@2026"
    test_full_name = f"Test Analyst {test_uid}"

    # -------------------------------------------------------------------------
    # TEST 1: Register New User
    # -------------------------------------------------------------------------
    print("\n[TEST 1] Registering fresh user (POST /api/v1/auth/register)...")
    reg_payload = {
        "email": test_email,
        "username": test_username,
        "password": test_password,
        "full_name": test_full_name,
        "role": "analyst",
    }
    reg_res = client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201, f"Expected 201 Created, got {reg_res.status_code}: {reg_res.text}"
    reg_data = reg_res.json()
    assert "access_token" in reg_data, "Response missing access_token"
    assert reg_data["token_type"] == "bearer", "Token type must be bearer"
    assert reg_data["user"]["email"] == test_email.lower(), "Returned email mismatch"
    assert reg_data["user"]["username"] == test_username, "Returned username mismatch"
    assert "hashed_password" not in reg_data["user"], "SECURITY ISSUE: hashed_password exposed in response!"
    print(f"      [PASS] User created with ID: {reg_data['user']['id']}")
    print(f"      [PASS] JWT Access Token issued: {reg_data['access_token'][:25]}...")

    # -------------------------------------------------------------------------
    # TEST 2: Duplicate Email Rejection
    # -------------------------------------------------------------------------
    print("\n[TEST 2] Verifying duplicate email rejection...")
    dup_email_payload = {
        "email": test_email.upper(),  # case-insensitive check
        "username": f"other_{test_uid}",
        "password": "Password123!",
    }
    dup_res = client.post("/api/v1/auth/register", json=dup_email_payload)
    assert dup_res.status_code == 400, f"Expected 400 Bad Request, got {dup_res.status_code}"
    assert "email" in dup_res.json()["detail"].lower()
    print("      [PASS] Duplicate email rejected with 400 Bad Request.")

    # -------------------------------------------------------------------------
    # TEST 3: Duplicate Username Rejection
    # -------------------------------------------------------------------------
    print("\n[TEST 3] Verifying duplicate username rejection...")
    dup_user_payload = {
        "email": f"new_{test_uid}@retailkpi.com",
        "username": test_username.upper(),  # case-insensitive check
        "password": "Password123!",
    }
    dup_u_res = client.post("/api/v1/auth/register", json=dup_user_payload)
    assert dup_u_res.status_code == 400, f"Expected 400 Bad Request, got {dup_u_res.status_code}"
    assert "username" in dup_u_res.json()["detail"].lower()
    print("      [PASS] Duplicate username rejected with 400 Bad Request.")

    # -------------------------------------------------------------------------
    # TEST 4: Login with Seed User (analyst@retailkpi.com)
    # -------------------------------------------------------------------------
    print("\n[TEST 4] Authenticating existing seed analyst (POST /api/v1/auth/login)...")
    login_payload = {
        "username": "analyst@retailkpi.com",
        "password": "Analyst@2026",
    }
    login_res = client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200, f"Expected 200 OK, got {login_res.status_code}: {login_res.text}"
    login_data = login_res.json()
    analyst_token = login_data["access_token"]
    assert login_data["user"]["role"] == "analyst"
    print(f"      [PASS] Analyst logged in successfully. Token: {analyst_token[:25]}...")

    # -------------------------------------------------------------------------
    # TEST 5: Login with Invalid Password
    # -------------------------------------------------------------------------
    print("\n[TEST 5] Verifying invalid password rejection...")
    bad_login_payload = {
        "username": "analyst@retailkpi.com",
        "password": "IncorrectPassword!@#",
    }
    bad_login_res = client.post("/api/v1/auth/login", json=bad_login_payload)
    assert bad_login_res.status_code == 401, f"Expected 401 Unauthorized, got {bad_login_res.status_code}"
    print("      [PASS] Invalid password rejected with 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # TEST 6: Login with Nonexistent User
    # -------------------------------------------------------------------------
    print("\n[TEST 6] Verifying nonexistent user rejection...")
    ghost_payload = {
        "username": "ghost_nonexistent@retailkpi.com",
        "password": "Password123!",
    }
    ghost_res = client.post("/api/v1/auth/login", json=ghost_payload)
    assert ghost_res.status_code == 401, f"Expected 401 Unauthorized, got {ghost_res.status_code}"
    print("      [PASS] Nonexistent user rejected with 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # TEST 7: Protected Route Without Token (GET /api/v1/auth/me)
    # -------------------------------------------------------------------------
    print("\n[TEST 7] Accessing protected route without credentials...")
    unauth_res = client.get("/api/v1/auth/me")
    assert unauth_res.status_code == 401, f"Expected 401 Unauthorized, got {unauth_res.status_code}"
    print("      [PASS] Unauthenticated request blocked with 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # TEST 8: Protected Route with Tampered/Invalid Token
    # -------------------------------------------------------------------------
    print("\n[TEST 8] Accessing protected route with forged token...")
    forged_headers = {"Authorization": "Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.forged.token"}
    forged_res = client.get("/api/v1/auth/me", headers=forged_headers)
    assert forged_res.status_code == 401, f"Expected 401 Unauthorized, got {forged_res.status_code}"
    print("      [PASS] Forged token rejected with 401 Unauthorized.")

    # -------------------------------------------------------------------------
    # TEST 9: Protected Route with Valid Bearer Token (GET /api/v1/auth/me)
    # -------------------------------------------------------------------------
    print("\n[TEST 9] Accessing protected profile with valid Bearer token...")
    auth_headers = {"Authorization": f"Bearer {analyst_token}"}
    me_res = client.get("/api/v1/auth/me", headers=auth_headers)
    assert me_res.status_code == 200, f"Expected 200 OK, got {me_res.status_code}: {me_res.text}"
    profile = me_res.json()
    assert profile["email"] == "analyst@retailkpi.com"
    assert profile["role"] == "analyst"
    assert profile["is_active"] is True
    print(f"      [PASS] Profile retrieved: {profile['full_name']} | Role: {profile['role']}")

    # -------------------------------------------------------------------------
    # TEST 10: Admin Authentication & Privileges
    # -------------------------------------------------------------------------
    print("\n[TEST 10] Authenticating Administrator account (admin@retailkpi.com)...")
    admin_login = {
        "username": "admin@retailkpi.com",
        "password": "Admin@2026",
    }
    admin_res = client.post("/api/v1/auth/login", json=admin_login)
    assert admin_res.status_code == 200, f"Expected 200 OK, got {admin_res.status_code}"
    admin_data = admin_res.json()
    admin_token = admin_data["access_token"]
    assert admin_data["user"]["role"] == "admin"
    assert admin_data["user"]["is_superuser"] is True
    print(f"      [PASS] Administrator authenticated. Role: {admin_data['user']['role']} (Superuser: True)")

    # -------------------------------------------------------------------------
    # TEST 11: Protected Logout Endpoint (POST /api/v1/auth/logout)
    # -------------------------------------------------------------------------
    print("\n[TEST 11] Invoking logout endpoint (POST /api/v1/auth/logout)...")
    logout_res = client.post("/api/v1/auth/logout", headers={"Authorization": f"Bearer {admin_token}"})
    assert logout_res.status_code == 200, f"Expected 200 OK, got {logout_res.status_code}"
    logout_msg = logout_res.json()["message"]
    assert "admin" in logout_msg
    print(f"      [PASS] Logout endpoint acknowledged: {logout_msg}")

    # -------------------------------------------------------------------------
    # Clean up test user created in Test 1
    # -------------------------------------------------------------------------
    db = SessionLocal()
    try:
        created_user = db.query(User).filter(User.email == test_email.lower()).first()
        if created_user:
            db.delete(created_user)
            db.commit()
            print("\n[CLEANUP] Ephemeral test user deleted successfully.")
    finally:
        db.close()

    print("\n" + "=" * 65)
    print("ALL 11 PHASE 4 AUTHENTICATION TESTS PASSED SUCCESSFULLY!")
    print("=" * 65)


if __name__ == "__main__":
    test_phase4_authentication()
