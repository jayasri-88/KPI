import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import InventoryAlertItem, InventoryResponse, InventoryUpdate, PaginatedResponse
from app.services import inventory_service

router = APIRouter()


class RestockRequest(BaseModel):
    quantity: int = Field(..., gt=0, description="Quantity of units to add to inventory")


@router.get(
    "",
    response_model=PaginatedResponse[InventoryResponse],
    summary="List store inventory",
    description="Returns store-level product stock tracking with status filters (In Stock, Low Stock, Out of Stock).",
)
def list_inventory(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    store_id: Optional[uuid.UUID] = Query(None, description="Store UUID"),
    product_id: Optional[uuid.UUID] = Query(None, description="Product UUID"),
    stock_status: Optional[str] = Query(None, description="In Stock, Low Stock, Out of Stock"),
    search: Optional[str] = Query(None, description="Search product name, SKU, or store"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return inventory_service.get_inventory(
        db=db,
        page=page,
        size=size,
        store_id=store_id,
        product_id=product_id,
        stock_status=stock_status,
        search=search,
    )


@router.get(
    "/alerts",
    response_model=List[InventoryAlertItem],
    summary="Get low-stock inventory alerts",
    description="Returns all product-store inventory rows that have breached reorder thresholds (Warning or Critical).",
)
def get_inventory_alerts(
    store_id: Optional[uuid.UUID] = Query(None, description="Filter alerts by Store UUID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return inventory_service.get_inventory_alerts(db=db, store_id=store_id)


@router.put(
    "/{inventory_id}",
    response_model=InventoryResponse,
    summary="Update inventory thresholds",
    description="Updates stock quantities and reorder point/quantity thresholds.",
)
def update_inventory(
    inventory_id: uuid.UUID,
    inv_in: InventoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = inventory_service.update_inventory(db=db, inventory_id=inventory_id, inv_in=inv_in)
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory '{inventory_id}' not found.")
    resp = InventoryResponse.model_validate(inv)
    resp.store_name = inv.store.name if inv.store else None
    resp.product_name = inv.product.product_name if inv.product else None
    resp.sku_code = inv.product.sku_code if inv.product else None
    return resp


@router.post(
    "/{inventory_id}/restock",
    response_model=InventoryResponse,
    summary="Restock inventory item",
    description="Adds units to existing on-hand stock and updates restocked timestamp.",
)
def restock_inventory(
    inventory_id: uuid.UUID,
    restock_in: RestockRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    inv = inventory_service.restock_inventory(
        db=db,
        inventory_id=inventory_id,
        quantity_added=restock_in.quantity,
    )
    if not inv:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Inventory '{inventory_id}' not found.")
    resp = InventoryResponse.model_validate(inv)
    resp.store_name = inv.store.name if inv.store else None
    resp.product_name = inv.product.product_name if inv.product else None
    resp.sku_code = inv.product.sku_code if inv.product else None
    return resp
