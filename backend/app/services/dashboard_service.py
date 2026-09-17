from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal


def get_dashboard_overview() -> dict:
    db = SessionLocal()
    try:
        # Total revenue from order_items
        total_revenue_result = db.query(func.sum(OrderItem.total_price)).scalar()
        total_revenue = float(total_revenue_result) if total_revenue_result else 0.0
        
        # Total orders
        total_orders = db.query(func.count(Order.id)).scalar()
        
        # Total items sold
        total_units_result = db.query(func.sum(OrderItem.quantity)).scalar()
        total_units = int(total_units_result) if total_units_result else 0
        
        # Total transactions (distinct orders)
        total_transactions = int(total_orders) if total_orders else 0
        
        # Average discount
        avg_discount_result = db.query(func.avg(OrderItem.discount_percent)).scalar()
        avg_discount = round(float(avg_discount_result), 2) if avg_discount_result else 0.0
        
        # Total products
        total_products = db.query(func.count(Product.id)).scalar()
        
        # Total retailers
        total_retailers = db.query(func.count(Store.id)).scalar()
        
        # Top category
        top_category_result = (
            db.query(
                Product.category_id,
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
            )
            .join(OrderItem, Product.id == OrderItem.product_id)
            .group_by(Product.category_id)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .first()
        )
        
        top_category_id = top_category_result[0] if top_category_result else None
        top_category_name = None
        top_category_revenue = 0.0
        
        if top_category_result and top_category_result[0]:
            from app.models import Category
            cat = db.query(Category).filter(Category.id == top_category_result[0]).first()
            if cat:
                top_category_name = cat.name
                top_category_revenue = round(float(top_category_result[1]), 2)
        
        # Top region
        top_region_result = (
            db.query(
                Store.region,
                func.sum(OrderItem.quantity * OrderItem.unit_price).label("revenue"),
            )
            .join(Order, Store.id == Order.store_id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .group_by(Store.region)
            .order_by(func.sum(OrderItem.quantity * OrderItem.unit_price).desc())
            .first()
        )
        
        top_region = top_region_result[0] if top_region_result else None
        top_region_revenue = 0.0
        if top_region_result:
            top_region_revenue = round(float(top_region_result[1]), 2)
        
        # Monthly sales
        monthly_result = (
            db.query(
                func.strftime("%Y-%m", Order.created_at).label("month"),
                func.sum(OrderItem.total_price).label("revenue"),
                func.count(func.distinct(Order.id)).label("transactions"),
                func.sum(OrderItem.quantity).label("units"),
            )
            .join(OrderItem, Order.id == OrderItem.order_id)
            .group_by(func.strftime("%Y-%m", Order.created_at))
            .order_by(func.strftime("%Y-%m", Order.created_at))
            .all()
        )
        
        monthly_sales = [
            {
                "month": item[0],
                "revenue": round(float(item[1]), 2),
                "transactions": int(item[2]),
                "units": int(item[3]),
            }
            for item in monthly_result
        ]
        
        return {
            "total_revenue": round(total_revenue, 2),
            "total_units": total_units,
            "total_transactions": total_transactions,
            "avg_discount": avg_discount,
            "total_products": int(total_products) if total_products else 0,
            "total_retailers": int(total_retailers) if total_retailers else 0,
            "top_category": top_category_name or "N/A",
            "top_category_revenue": top_category_revenue,
            "top_region": top_region or "N/A",
            "top_region_revenue": top_region_revenue,
            "monthly_sales": monthly_sales,
        }
    finally:
        db.close()