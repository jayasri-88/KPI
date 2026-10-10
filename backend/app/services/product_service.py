import math
import uuid
from decimal import Decimal
from typing import Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session, joinedload

from app.core.security import escape_like
from app.models import Category, Product
from app.schemas import PaginatedResponse, ProductCreate, ProductResponse, ProductUpdate


def get_products(
    db: Session,
    page: int = 1,
    size: int = 20,
    category_id: Optional[uuid.UUID] = None,
    brand: Optional[str] = None,
    min_price: Optional[Decimal] = None,
    max_price: Optional[Decimal] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    sort_by: str = "product_name",
    sort_desc: bool = False,
) -> PaginatedResponse[ProductResponse]:
    query = (
        db.query(Product)
        .options(joinedload(Product.category))
    )

    if category_id:
        query = query.filter(Product.category_id == category_id)
    if brand:
        query = query.filter(func.lower(Product.brand) == brand.strip().lower())
    if min_price is not None:
        query = query.filter(Product.unit_price >= min_price)
    if max_price is not None:
        query = query.filter(Product.unit_price <= max_price)
    if is_active is not None:
        query = query.filter(Product.is_active == is_active)
    if search:
        s = f"%{escape_like(search.strip().lower())}%"
        query = query.filter(
            or_(
                func.lower(Product.product_name).like(s),
                func.lower(Product.sku_code).like(s),
                func.lower(Product.brand).like(s),
            )
        )

    # Sorting
    sort_column = getattr(Product, sort_by, Product.product_name)
    if sort_desc:
        query = query.order_by(sort_column.desc())
    else:
        query = query.order_by(sort_column.asc())

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    products = query.offset(offset).limit(size).all()

    items = []
    for p in products:
        resp = ProductResponse.model_validate(p)
        resp.category_name = p.category.name if p.category else None
        items.append(resp)

    return PaginatedResponse[ProductResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_product_by_id(db: Session, product_id: uuid.UUID) -> Optional[Product]:
    return db.query(Product).filter(Product.id == product_id).first()


def get_product_by_sku(db: Session, sku_code: str) -> Optional[Product]:
    return db.query(Product).filter(func.lower(Product.sku_code) == sku_code.strip().lower()).first()


def create_product(db: Session, prod_in: ProductCreate) -> Product:
    product = Product(
        sku_code=prod_in.sku_code.strip().upper(),
        product_name=prod_in.product_name.strip(),
        description=prod_in.description,
        category_id=prod_in.category_id,
        brand=prod_in.brand.strip(),
        unit_price=prod_in.unit_price,
        cost_price=prod_in.cost_price,
        is_active=prod_in.is_active,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(
    db: Session,
    product_id: uuid.UUID,
    prod_in: ProductUpdate,
) -> Optional[Product]:
    product = get_product_by_id(db, product_id)
    if not product:
        return None

    update_data = prod_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        if field == "sku_code" and value:
            value = value.strip().upper()
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: uuid.UUID) -> bool:
    product = get_product_by_id(db, product_id)
    if not product:
        return False
    db.delete(product)
    db.commit()
    return True
