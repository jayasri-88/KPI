"""
Pytest Fixtures and Global Configurations for Retail KPI Test Suite
"""

import sys
import os
from pathlib import Path
import pytest
from fastapi.testclient import TestClient

# Ensure backend root is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app
from app.database import SessionLocal
from app.models import User, Store, Product, Category
from app.core.security import create_access_token


@pytest.fixture(scope="session")
def client():
    """Provides a reusable FastAPI TestClient instance."""
    with TestClient(app) as c:
        yield c


@pytest.fixture(scope="function")
def db():
    """Provides a scoped database session with automatic cleanup."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


@pytest.fixture(scope="session")
def admin_user():
    """Fetches or returns admin user details."""
    session = SessionLocal()
    try:
        user = session.query(User).filter(User.role == "admin").first()
        if not user:
            user = session.query(User).first()
        return {
            "id": str(user.id),
            "email": user.email,
            "username": user.username,
            "role": user.role,
        }
    finally:
        session.close()


@pytest.fixture(scope="session")
def admin_token(admin_user):
    """Generates a valid JWT access token for admin user."""
    return create_access_token(
        subject=admin_user["id"],
        extra_claims={
            "email": admin_user["email"],
            "username": admin_user["username"],
            "role": admin_user["role"],
        },
    )


@pytest.fixture(scope="session")
def auth_headers(admin_token):
    """Provides authorization header for protected endpoints."""
    return {"Authorization": f"Bearer {admin_token}"}
