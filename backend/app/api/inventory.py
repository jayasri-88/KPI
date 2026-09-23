from fastapi import APIRouter

from app.services.inventory_service import (
    get_inventory_alerts,
    get_inventory_summary,
)


router = APIRouter(
    tags=["Inventory"],
)


@router.get("/alerts")
def inventory_alerts():
    return {
        "data": get_inventory_alerts()
    }


@router.get("/summary")
def inventory_summary():
    return get_inventory_summary()