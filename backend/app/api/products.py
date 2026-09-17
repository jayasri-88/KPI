from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.database import get_db
from app.models import Product, Category
from app.schemas import ProductSchema, ProductCreate, ProductUpdate, CategorySchema
from typing import List, Optional


router = APIRouter(tags=["Products"])


@router.get("/", response_model=List[ProductSchema])
def list_products(
    skip: int = 0,
    limit: int = 100,
    category_id: str = None,
    search: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Product)
    if category_id:
        query = query.filter(Product.category_id == category_id)
    if search:
        query = query.filter(
            (Product.product_name.ilike(f"%{search}%"))
            | (Product.sku_code.ilike(f"%{search}%"))
        )
    
    products = query.offset(skip).limit(limit).all()
    total = query.count()
    return {"items": products, "total": total, "skip": skip, "limit": limit}


@router.get("/{product_id}", response_model=ProductSchema)
def get_product(product_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    product = db.query(Product).filter(Product.id == UUID(product_id)).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    return product


@router.post("/", response_model=ProductSchema)
def create_product(product: ProductCreate, db: Session = Depends(get_db)):
    # Check category exists if provided
    if product.category_id:
        from sqlalchemy import UUID
        category = db.query(Category).filter(Category.id == UUID(product.category_id)).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    db_product = Product(
        sku_code=product.sku_code,
        product_name=product.product_name,
        description=product.description,
        category_id=product.category_id,
        brand=product.brand,
        unit_price=product.unit_price,
        cost_price=product.cost_price,
        must_sell_flag=product.must_sell_flag,
        launch_date=product.launch_date,
        is_active=product.is_active if product.is_active is not None else True,
    )
    db.add(db_product)
    db.commit()
    db.refresh(db_product)
    return db_product


@router.put("/{product_id}", response_model=ProductSchema)
def update_product(product_id: str, product: ProductUpdate, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    db_product = db.query(Product).filter(Product.id == UUID(product_id)).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    update_data = product.dict(exclude_unset=True)
    if "category_id" in update_data and update_data["category_id"]:
        category = db.query(Category).filter(Category.id == UUID(update_data["category_id"])).first()
        if not category:
            raise HTTPException(status_code=404, detail="Category not found")
    
    for key, value in update_data.items():
        setattr(db_product, key, value)
    
    db.commit()
    db.refresh(db_product)
    return db_product


@router.delete("/{product_id}", response_model=dict)
def delete_product(product_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    db_product = db.query(Product).filter(Product.id == UUID(product_id)).first()
    if not db_product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Check if product has order items
    from app.models import OrderItem
    order_items = db.query(OrderItem).filter(OrderItem.product_id == UUID(product_id)).first()
    if order_items:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete product: has existing order items",
        )
    
    db.delete(db_product)
    db.commit()
    return {"message": "Product deleted successfully"}


@router.get("/category/{category_id}", response_model=List[ProductSchema])
def get_products_by_category(category_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    products = db.query(Product).filter(Product.category_id == UUID(category_id)).all()
    return products