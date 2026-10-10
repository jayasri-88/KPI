import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import OrderCreate, OrderDetailResponse, OrderResponse, PaginatedResponse
from app.services import order_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[OrderResponse],
    summary="List retail orders",
    description="Returns paginated sales orders with date range, store, customer, status, and channel filters.",
)
def list_orders(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    store_id: Optional[uuid.UUID] = Query(None, description="Store UUID"),
    customer_id: Optional[uuid.UUID] = Query(None, description="Customer UUID"),
    status: Optional[str] = Query(None, description="Order status: completed, returned, cancelled"),
    channel: Optional[str] = Query(None, description="Channel: In-Store, Online, Express Delivery"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    min_amount: Optional[Decimal] = Query(None, ge=0, description="Minimum order total"),
    max_amount: Optional[Decimal] = Query(None, ge=0, description="Maximum order total"),
    sort_desc: bool = Query(True, description="Sort descending by date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return order_service.get_orders(
        db=db,
        page=page,
        size=size,
        store_id=store_id,
        customer_id=customer_id,
        status=status,
        channel=channel,
        start_date=start_date,
        end_date=end_date,
        min_amount=min_amount,
        max_amount=max_amount,
        sort_desc=sort_desc,
    )


@router.get(
    "/{order_id}",
    response_model=OrderDetailResponse,
    summary="Get order details",
    description="Retrieves a complete order receipt including line items, discounts, and tax calculation.",
)
def get_order(
    order_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    order = order_service.get_order_by_id(db=db, order_id=order_id)
    if not order:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Order '{order_id}' not found.")
    return order


@router.post(
    "",
    response_model=OrderDetailResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create retail order",
    description="Submits a new multi-item transaction, computes GST tax and totals, and updates customer metrics.",
)
def create_order(
    order_in: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        return order_service.create_order(db=db, order_in=order_in)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
