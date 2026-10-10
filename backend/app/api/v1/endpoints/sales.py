import uuid
from datetime import datetime
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import PaginatedResponse, SaleResponse, SalesSummary
from app.services import sales_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[SaleResponse],
    summary="List sales records",
    description="Returns itemized sales with revenue, COGS, gross profit, and margin % calculations.",
)
def list_sales(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    store_id: Optional[uuid.UUID] = Query(None, description="Store UUID"),
    product_id: Optional[uuid.UUID] = Query(None, description="Product UUID"),
    channel: Optional[str] = Query(None, description="Sales channel"),
    start_date: Optional[datetime] = Query(None, description="Start date filter (ISO format)"),
    end_date: Optional[datetime] = Query(None, description="End date filter (ISO format)"),
    min_revenue: Optional[Decimal] = Query(None, ge=0, description="Minimum revenue filter"),
    max_revenue: Optional[Decimal] = Query(None, ge=0, description="Maximum revenue filter"),
    sort_by: str = Query("sale_date", description="Field to sort by"),
    sort_desc: bool = Query(True, description="Sort descending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return sales_service.get_sales(
        db=db,
        page=page,
        size=size,
        store_id=store_id,
        product_id=product_id,
        channel=channel,
        start_date=start_date,
        end_date=end_date,
        min_revenue=min_revenue,
        max_revenue=max_revenue,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.get(
    "/summary",
    response_model=SalesSummary,
    summary="Get aggregated sales summary",
    description="Calculates consolidated total revenue, total COGS, gross profit, margin %, and average order value.",
)
def get_sales_summary(
    start_date: Optional[datetime] = Query(None, description="Start date filter"),
    end_date: Optional[datetime] = Query(None, description="End date filter"),
    store_id: Optional[uuid.UUID] = Query(None, description="Store filter"),
    product_id: Optional[uuid.UUID] = Query(None, description="Product filter"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return sales_service.get_sales_summary(
        db=db,
        start_date=start_date,
        end_date=end_date,
        store_id=store_id,
        product_id=product_id,
    )


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    summary="Get single sale record",
    description="Retrieves a specific financial sale record by UUID.",
)
def get_sale(
    sale_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    sale = sales_service.get_sale_by_id(db=db, sale_id=sale_id)
    if not sale:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Sale '{sale_id}' not found.")
    resp = SaleResponse.model_validate(sale)
    resp.store_name = sale.store.name if sale.store else None
    resp.product_name = sale.product.product_name if sale.product else None
    resp.sku_code = sale.product.sku_code if sale.product else None
    return resp
