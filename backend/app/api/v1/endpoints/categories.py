import uuid
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_admin, get_current_user
from app.database import get_db
from app.models import User
from app.schemas import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services import category_service

router = APIRouter()


@router.get(
    "",
    response_model=List[CategoryResponse],
    summary="List product categories",
    description="Returns all merchandise categories with target gross margin percentages.",
)
def list_categories(
    is_active: Optional[bool] = Query(None, description="Filter active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return category_service.get_categories(db=db, is_active=is_active)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Get category by ID",
    description="Retrieves a merchandise category profile.",
)
def get_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cat = category_service.get_category_by_id(db=db, category_id=category_id)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category '{category_id}' not found.")
    return CategoryResponse.model_validate(cat)


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create category",
    description="Creates a new merchandise department. Admin only.",
)
def create_category(
    cat_in: CategoryCreate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    existing = category_service.get_category_by_code(db=db, code=cat_in.code)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with code '{cat_in.code}' already exists.",
        )
    return CategoryResponse.model_validate(category_service.create_category(db=db, cat_in=cat_in))


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    summary="Update category",
    description="Updates a category name or margin targets. Admin only.",
)
def update_category(
    category_id: uuid.UUID,
    cat_in: CategoryUpdate,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    cat = category_service.update_category(db=db, category_id=category_id, cat_in=cat_in)
    if not cat:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category '{category_id}' not found.")
    return CategoryResponse.model_validate(cat)


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete category",
    description="Deletes a category. Admin only.",
)
def delete_category(
    category_id: uuid.UUID,
    db: Session = Depends(get_db),
    admin_user: User = Depends(get_current_active_admin),
):
    deleted = category_service.delete_category(db=db, category_id=category_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Category '{category_id}' not found.")
    return None
