import uuid
from typing import List, Optional
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.models import Category
from app.schemas import CategoryCreate, CategoryResponse, CategoryUpdate


def get_categories(
    db: Session,
    is_active: Optional[bool] = None,
) -> List[CategoryResponse]:
    query = db.query(Category)
    if is_active is not None:
        query = query.filter(Category.is_active == is_active)
    categories = query.order_by(Category.name.asc()).all()
    return [CategoryResponse.model_validate(c) for c in categories]


def get_category_by_id(db: Session, category_id: uuid.UUID) -> Optional[Category]:
    return db.query(Category).filter(Category.id == category_id).first()


def get_category_by_code(db: Session, code: str) -> Optional[Category]:
    return db.query(Category).filter(func.lower(Category.code) == code.strip().lower()).first()


def create_category(db: Session, cat_in: CategoryCreate) -> Category:
    category = Category(
        name=cat_in.name.strip(),
        code=cat_in.code.strip().upper(),
        description=cat_in.description,
        target_margin_pct=cat_in.target_margin_pct,
        is_active=cat_in.is_active,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(
    db: Session,
    category_id: uuid.UUID,
    cat_in: CategoryUpdate,
) -> Optional[Category]:
    cat = get_category_by_id(db, category_id)
    if not cat:
        return None

    update_data = cat_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "code" and value:
            value = value.strip().upper()
        setattr(cat, field, value)

    db.commit()
    db.refresh(cat)
    return cat


def delete_category(db: Session, category_id: uuid.UUID) -> bool:
    cat = get_category_by_id(db, category_id)
    if not cat:
        return False
    db.delete(cat)
    db.commit()
    return True
