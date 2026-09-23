from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Product, OrderItem, Store, Order, Sales


def get_sales_trend() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                func.to_char(Sales.date, 'YYYY-MM').label("month"),
                func.sum(Sales.revenue).label("revenue"),
                func.sum(Sales.quantity).label("units"),
                func.count(Sales.id).label("transactions"),
            )
            .group_by(func.to_char(Sales.date, 'YYYY-MM'))
            .order_by(func.to_char(Sales.date, 'YYYY-MM'))
            .all()
        )
        
        return [
            {
                "month": item[0],
                "revenue": round(float(item[1]) if item[1] else 0, 2),
                "units": int(item[2]) if item[2] else 0,
                "transactions": int(item[3]) if item[3] else 0,
            }
            for item in results
        ]
    finally:
        db.close()


def get_category_performance() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                Product.category_id,
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
                func.sum(OrderItem.quantity).label("units"),
                func.count(func.distinct(OrderItem.id)).label("transactions"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Product.category_id)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .all()
        )
        
        # Fetch category names
        from app.models import Category
        category_map = {str(c.id): c.name for c in db.query(Category).all()}
        
        return [
            {
                "category": category_map.get(str(item[0]), "Uncategorized"),
                "revenue": round(float(item[1]), 2),
                "units": int(item[2]) if item[2] else 0,
                "transactions": int(item[3]) if item[3] else 0,
            }
            for item in results
        ]
    finally:
        db.close()


def get_sku_performance() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                OrderItem.product_id,
                Product.sku_code,
                Product.product_name,
                Product.category_id,
                func.sum(OrderItem.quantity).label("units"),
                func.sum(OrderItem.total_price).label("revenue"),
                func.avg(OrderItem.discount_percent).label("avg_discount"),
                func.count(Order.id).label("transactions"),
            )
            .join(Product, OrderItem.product_id == Product.id)
            .outerjoin(Order, OrderItem.order_id == Order.id)
            .group_by(OrderItem.product_id, Product.sku_code, Product.product_name, Product.category_id)
            .order_by(func.sum(OrderItem.total_price).desc())
            .all()
        )
        
        return [
            {
                "product_id": str(item[0]) if item[0] else "",
                "sku_code": item[1] or "",
                "product_name": item[2] or "",
                "category": str(item[3]) if item[3] else "",
                "revenue": round(float(item[5]) if item[5] else 0, 2),
                "units": int(item[4]) if item[4] else 0,
                "transactions": int(item[7]) if item[7] else 0,
                "avg_discount": round(float(item[6]) if item[6] else 0, 2),
            }
            for item in results
        ]
    finally:
        db.close()


def get_region_performance() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                Store.region,
                func.sum(OrderItem.total_price).label("revenue"),
                func.sum(OrderItem.quantity).label("units"),
                func.count(func.distinct(Order.id)).label("transactions"),
                func.count(func.distinct(Store.id)).label("retailer_count"),
            )
            .join(Order, Store.id == Order.store_id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .group_by(Store.region)
            .order_by(func.sum(OrderItem.total_price).desc())
            .all()
        )
        
        return [
            {
                "region": item[0] or "Unknown",
                "revenue": round(float(item[1]) if item[1] else 0, 2),
                "units": int(item[2]) if item[2] else 0,
                "transactions": int(item[3]) if item[3] else 0,
                "retailer_count": int(item[4]) if item[4] else 0,
            }
            for item in results
        ]
    finally:
        db.close()