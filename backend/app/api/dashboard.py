from fastapi import APIRouter

from app.services.dashboard_service import (
    get_dashboard_overview,
)
router = APIRouter(
    tags=["Dashboard"],
)


@router.get("/overview")
def dashboard_overview():
    return get_dashboard_overview()