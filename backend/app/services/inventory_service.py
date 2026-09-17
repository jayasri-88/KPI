from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Product, Inventory, Store


def get_inventory_alerts() -> list:
    db = SessionLocal()
    try:
        # Get latest inventory dates per product-retailer combination
        latest_dates = (
            db.query(
                Inventory.retailer_id,
                Inventory.product_id,
                func.max(Inventory.last_updated).label("latest_date"),
            )
            .group_by(Inventory.retailer_id, Inventory.product_id)
            .subquery()
        )
        
        # Get current inventory with stock levels
        results = (
            db.query(Inventory, Product, Store)
            .join(Product, Inventory.product_id == Product.id)
            .join(Store, Inventory.retailer_id == Store.retailer_id)
            .join(latest_dates,
                  (Inventory.retaler_id == latest_dates.c.retailer_id)
                  & (Inventory.product_id == latest_dates.c.product_id)
                  & (func.date(Inventory.last_updated) == func.date(latest_dates.c.latest_date)))
            .all()
        )
        
        # Simplified - just get all inventory and find low stock
        inventory_items = db.query(Inventory).all()
        
        alerts = []
        for item in inventory_items:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if not product:
                continue
            
            stock_ratio = 1.0
            if item.quantity_on_hand > 0 and item.reorder_point > 0:
                stock_ratio = item.quantity_on_hand / item.reorder_point
            
            if item.quantity_on_hand == 0:
                severity = "critical"
            elif stock_ratio <= 0.5:
                severity = "high"
            elif stock_ratio <= 1.0:
                severity = "warning"
            else:
                severity = "ok"
            
            alerts.append(
                {
                    "inventory_id": str(item.id),
                    "product_id": str(item.product_id),
                    "product_name": product.product_name if product else "Unknown",
                    "sku_code": product.sku_code if product else "UNKNOWN",
                    "retailer_id": item.retailer_id,
                    "retailer_name": "",
                    "city": "",
                    "region": "",
                    "stock_level": item.quantity_on_hand,
                    "reorder_point": item.reorder_point,
                    "stock_ratio": round(stock_ratio, 2),
                    "severity": severity,
                }
            )
        
        # Sort: critical first, then high, then warning
        severity_order = {"critical": 0, "high": 1, "warning": 2, "ok": 3}
        alerts.sort(key=lambda x: severity_order.get(x["severity"], 99))
        
        return alerts
    finally:
        db.close()


def get_inventory_summary() -> dict:
    db = SessionLocal()
    try:
        total_records = db.query(func.count(Inventory.id)).scalar() or 0
        
        # Get latest date
        latest = db.query(func.max(Inventory.last_updated)).scalar()
        
        if not latest:
            return {
                "latest_date": None,
                "total_records": 0,
                "total_alerts": 0,
                "critical_alerts": 0,
                "high_alerts": 0,
                "warning_alerts": 0,
            }
        
        # Count alerts (low stock)
        critical = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity_on_hand == 0
        ).scalar() or 0
        
        high = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity_on_hand > 0,
            Inventory.quantity_on_hand <= Inventory.reorder_point / 2
        ).scalar() or 0
        
        # Warning stock: between 50-100% of reorder point
        warning = db.query(func.count(Inventory.id)).filter(
            Inventory.quantity_on_hand > Inventory.reorder_point / 2,
            Inventory.quantity_on_hand < Inventory.reorder_point
        ).scalar() or 0
        
        total_alerts = critical + high + warning
        
        return {
            "latest_date": latest,
            "total_records": int(total_records),
            "total_alerts": int(total_alerts),
            "critical_alerts": int(critical),
            "high_alerts": int(high),
            "warning_alerts": int(warning),
        }
    finally:
        db.close()