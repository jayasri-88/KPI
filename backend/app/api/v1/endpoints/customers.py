import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database import get_db
from app.models import User
from app.schemas import CustomerCreate, CustomerResponse, CustomerUpdate, PaginatedResponse
from app.services import customer_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[CustomerResponse],
    summary="List retail customers",
    description="Returns paginated customers with cohort segmentation (VIP, Regular, New, At-Risk), spend filters, and sorting.",
)
def list_customers(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    segment: Optional[str] = Query(None, description="Segment: VIP, Regular, New, At-Risk"),
    city: Optional[str] = Query(None, description="City filter"),
    min_spend: Optional[Decimal] = Query(None, ge=0, description="Minimum lifetime spend"),
    max_spend: Optional[Decimal] = Query(None, ge=0, description="Maximum lifetime spend"),
    search: Optional[str] = Query(None, description="Search by name, email, or city"),
    sort_by: str = Query("total_spend", description="Sort by field: total_spend, total_orders_count, created_at"),
    sort_desc: bool = Query(True, description="Sort descending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return customer_service.get_customers(
        db=db,
        page=page,
        size=size,
        segment=segment,
        city=city,
        min_spend=min_spend,
        max_spend=max_spend,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.get(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Get customer by ID",
    description="Retrieves a customer profile with lifetime analytics and order history count.",
)
def get_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = customer_service.get_customer_by_id(db=db, customer_id=customer_id)
    if not cust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer '{customer_id}' not found.")
    return CustomerResponse.model_validate(cust)


@router.post(
    "",
    response_model=CustomerResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create customer",
    description="Registers a new retail shopper account.",
)
def create_customer(
    cust_in: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing = customer_service.get_customer_by_email(db=db, email=cust_in.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Customer with email '{cust_in.email}' already exists.",
        )
    return CustomerResponse.model_validate(customer_service.create_customer(db=db, cust_in=cust_in))


@router.put(
    "/{customer_id}",
    response_model=CustomerResponse,
    summary="Update customer",
    description="Updates customer contact information or cohort assignment.",
)
def update_customer(
    customer_id: uuid.UUID,
    cust_in: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cust = customer_service.update_customer(db=db, customer_id=customer_id, cust_in=cust_in)
    if not cust:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer '{customer_id}' not found.")
    return CustomerResponse.model_validate(cust)


@router.delete(
    "/{customer_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete customer",
    description="Deletes a customer profile.",
)
def delete_customer(
    customer_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    deleted = customer_service.delete_customer(db=db, customer_id=customer_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Customer '{customer_id}' not found.")
    return None
