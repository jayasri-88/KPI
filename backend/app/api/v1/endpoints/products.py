import uuid
from decimal import Decimal
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import PaginatedResponse, ProductCreate, ProductResponse, ProductUpdate
from app.services import product_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[ProductResponse],
    summary="List products",
    description="Returns paginated list of catalog products with category, brand, and price filtering.",
)
def list_products(
    page: int = Query(1, ge=1, description="Page number"),
    size: int = Query(20, ge=1, le=100, description="Items per page"),
    category_id: Optional[uuid.UUID] = Query(None, description="Category UUID"),
    brand: Optional[str] = Query(None, description="Brand name filter"),
    min_price: Optional[Decimal] = Query(None, ge=0, description="Minimum price filter"),
    max_price: Optional[Decimal] = Query(None, ge=0, description="Maximum price filter"),
    is_active: Optional[bool] = Query(None, description="Filter active status"),
    search: Optional[str] = Query(None, description="Search by product name, SKU, or brand"),
    sort_by: str = Query("product_name", description="Field to sort by"),
    sort_desc: bool = Query(False, description="Sort descending"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return product_service.get_products(
        db=db,
        page=page,
        size=size,
        category_id=category_id,
        brand=brand,
        min_price=min_price,
        max_price=max_price,
        is_active=is_active,
        search=search,
        sort_by=sort_by,
        sort_desc=sort_desc,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Get product by ID",
    description="Retrieves SKU details, pricing, and category information.",
)
def get_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    product = product_service.get_product_by_id(db=db, product_id=product_id)
    if not product:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found.")
    resp = ProductResponse.model_validate(product)
    resp.category_name = product.category.name if product.category else None
    return resp


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create product",
    description="Adds a new product to the catalog. Admin only.",
)
def create_product(
    prod_in: ProductCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    # Check duplicate SKU
    existing = product_service.get_product_by_sku(db=db, sku_code=prod_in.sku_code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU code '{prod_in.sku_code}' already exists.",
        )
    created = product_service.create_product(db=db, prod_in=prod_in)
    resp = ProductResponse.model_validate(created)
    resp.category_name = created.category.name if created.category else None
    return resp


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    summary="Update product",
    description="Updates product specifications or pricing. Admin only.",
)
def update_product(
    product_id: uuid.UUID,
    prod_in: ProductUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    updated = product_service.update_product(db=db, product_id=product_id, prod_in=prod_in)
    if not updated:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found.")
    resp = ProductResponse.model_validate(updated)
    resp.category_name = updated.category.name if updated.category else None
    return resp


@router.delete(
    "/{product_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete product",
    description="Deletes a product SKU from catalog. Admin only.",
)
def delete_product(
    product_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    deleted = product_service.delete_product(db=db, product_id=product_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Product '{product_id}' not found.")
    return None
