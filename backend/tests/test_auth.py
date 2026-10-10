"""
Authentication & Authorization Integration Tests
Verifies login success, bad credentials, missing headers, JWT validation, and registration guards.
"""

import uuid
import pytest
from app.core.security import create_access_token


def test_login_success(client):
    """Test successful login with verified credentials returns JWT token."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@retailkpi.com", "password": "Admin@2026"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert data["token_type"].lower() == "bearer"
    assert "user" in data
    assert data["user"]["email"] == "admin@retailkpi.com"
    assert data["user"]["role"] == "admin"


def test_login_invalid_password(client):
    """Test login failure with incorrect password returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "admin@retailkpi.com", "password": "WrongPassword999!"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_401"


def test_login_nonexistent_user(client):
    """Test login with non-existent user returns 401."""
    response = client.post(
        "/api/v1/auth/login",
        json={"username": "nonexistent_user_999@domain.com", "password": "AnyPassword123"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_401"


def test_unauthorized_request_no_token(client):
    """Test accessing protected route without Authorization header returns 401."""
    response = client.get("/api/v1/auth/me")
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_401"


def test_unauthorized_request_invalid_token(client):
    """Test accessing protected route with malformed or tampered token returns 401."""
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer this_is_a_forged_or_invalid_jwt_token"},
    )
    assert response.status_code == 401
    data = response.json()
    assert "error" in data
    assert data["error"]["code"] == "HTTP_401"


def test_get_current_user_profile(client, auth_headers):
    """Test authenticated user can access profile through /api/v1/auth/me."""
    response = client.get("/api/v1/auth/me", headers=auth_headers)
    assert response.status_code == 200
    profile = response.json()
    assert "id" in profile
    assert "email" in profile
    assert profile["role"] == "admin"


def test_register_duplicate_email(client):
    """Test registering a user with an already existing email returns 400."""
    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": "admin@retailkpi.com",
            "username": f"unique_user_{uuid.uuid4().hex[:6]}",
            "password": "ValidPassword@123",
            "full_name": "Test Duplication",
        },
    )
    assert response.status_code == 400
    data = response.json()
    assert "already exists" in data.get("detail", "").lower()
