from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Product, OrderItem, Store, Order, Sales, Category


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
                "month": row.month,
                "revenue": round(float(row.revenue), 2) if row.revenue else 0,
                "units": int(row.units) if row.units else 0,
                "transactions": int(row.transactions) if row.transactions else 0,
            }
            for row in results
        ]
    finally:
        db.close()


def get_category_performance() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                Category.name.label("category"),
                func.sum(OrderItem.total_price).label("revenue"),
                func.sum(OrderItem.quantity).label("units"),
                func.count(func.distinct(Order.id)).label("transactions"),
            )
            .join(Product, Product.category_id == Category.id)
            .join(OrderItem, Product.id == OrderItem.product_id)
            .join(Order, OrderItem.order_id == Order.id)
            .group_by(Category.id, Category.name)
            .order_by(func.sum(OrderItem.total_price).desc())
            .all()
        )
        
        return [
            {
                "category": row.category or "Uncategorized",
                "revenue": round(float(row.revenue), 2) if row.revenue else 0,
                "units": int(row.units) if row.units else 0,
                "transactions": int(row.transactions) if row.transactions else 0,
            }
            for row in results
        ]
    finally:
        db.close()


def get_sku_performance() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                OrderItem.product_id.label("product_id"),
                Product.sku_code.label("sku_code"),
                Product.product_name.label("product_name"),
                Category.name.label("category"),
                func.sum(OrderItem.quantity).label("units"),
                func.sum(OrderItem.total_price).label("revenue"),
                func.avg(OrderItem.discount_percent).label("avg_discount"),
                func.count(func.distinct(Order.id)).label("transactions"),
            )
            .join(Product, OrderItem.product_id == Product.id)
            .join(Order, OrderItem.order_id == Order.id)
            .outerjoin(Category, Product.category_id == Category.id)
            .group_by(OrderItem.product_id, Product.sku_code, Product.product_name, Category.name)
            .order_by(func.sum(OrderItem.total_price).desc())
            .all()
        )
        
        return [
            {
                "product_id": str(row.product_id) if row.product_id else "",
                "sku_code": row.sku_code or "",
                "product_name": row.product_name or "",
                "category": row.category or "Uncategorized",
                "revenue": round(float(row.revenue), 2) if row.revenue else 0,
                "units": int(row.units) if row.units else 0,
                "transactions": int(row.transactions) if row.transactions else 0,
                "avg_discount": round(float(row.avg_discount), 2) if row.avg_discount else 0,
            }
            for row in results
        ]
    finally:
        db.close()


def get_region_performance() -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                Store.region.label("region"),
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
                "region": row.region or "Unknown",
                "revenue": round(float(row.revenue), 2) if row.revenue else 0,
                "units": int(row.units) if row.units else 0,
                "transactions": int(row.transactions) if row.transactions else 0,
                "retailer_count": int(row.retailer_count) if row.retailer_count else 0,
            }
            for row in results
        ]
    finally:
        db.close()
