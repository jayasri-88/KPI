from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import SessionLocal
from app.models import Product, OrderItem, Store, Order


def get_sku_intelligence() -> dict:
    db = SessionLocal()
    try:
        total_skus = db.query(func.count(Product.id)).select_from(Product).scalar() or 0
        
        must_sell = (
            db.query(Product)
            .filter(Product.must_sell_flag == True)
            .all()
        )
        
        must_sell_skus = len(must_sell)
        
        # Get revenues for all SKUs
        revenues = (
            db.query(
                OrderItem.product_id,
                func.sum(OrderItem.total_price).label("revenue"),
                func.sum(OrderItem.quantity).label("units"),
            )
            .group_by(OrderItem.product_id)
            .order_by(func.sum(OrderItem.total_price).desc())
            .all()
        )
        
        if not revenues:
            return {
                "summary": {
                    "total_skus": total_skus,
                    "must_sell_skus": must_sell_skus,
                    "must_sell_adherence": 0,
                },
                "top_performers": [],
                "underperformers": [],
                "must_sell": [],
            }
        
        # Sort revenues to find percentile threshold
        revenue_values = sorted([float(r[1]) for r in revenues if r[1]], reverse=False)
        
        percentile_index = max(0, int(len(revenue_values) * 0.20) - 1)
        underperformer_threshold = revenue_values[percentile_index] if revenue_values else 0
        
        # Enrich with product details
        product_ids = [r[0] for r in revenues]
        products = {
            str(p.id): p for p in db.query(Product).filter(Product.id.in_(product_ids)).all()
        }
        
        enriched = []
        for rank, item in enumerate(revenues, start=1):
            product = products.get(str(item[0]), {})
            enriched.append(
                {
                    "rank": rank,
                    "product_id": str(item[0]) if item[0] else "",
                    "sku_code": product.sku_code if product else "",
                    "product_name": product.product_name if product else "",
                    "category": product.category_id if product else "",
                    "sub_category": "",
                    "brand": product.brand if product else "",
                    "must_sell_flag": product.must_sell_flag if product else False,
                    "revenue": round(float(item[1]) if item[1] else 0, 2),
                    "units": int(item[2]) if item[2] else 0,
                    "transactions": 0,  # Would need order join
                    "avg_discount": 0,  # Would need discount data
                    "underperformer": float(item[1]) if item[1] else 0 <= underperformer_threshold,
                }
            )
        
        top_performers = enriched[:10]
        
        underperformers = [
            item for item in enriched if item["underperformer"]
        ][:10]
        
        must_sell_performers = [
            item for item in enriched if item["must_sell_flag"]
        ]
        
        selling_must_sell = [
            item for item in must_sell_performers if item["units"] > 0
        ]
        
        adherence = (
            len(selling_must_sell) / len(must_sell_performers) * 100
            if must_sell_performers else 0
        )
        
        return {
            "summary": {
                "total_skus": total_skus,
                "must_sell_skus": must_sell_skus,
                "must_sell_adherence": round(adherence, 2),
                "underperformer_threshold": round(underperformer_threshold, 2),
            },
            "top_performers": top_performers,
            "underperformers": underperformers,
            "must_sell": must_sell_performers,
        }
    finally:
        db.close()


def get_sku_region_comparison(product_id: int) -> list:
    db = SessionLocal()
    try:
        results = (
            db.query(
                Store.region,
                func.sum(OrderItem.total_price).label("revenue"),
                func.sum(OrderItem.quantity).label("units"),
                func.count(Order.id).label("transactions"),
                func.avg(OrderItem.discount_percent).label("avg_discount"),
            )
            .join(Order, Store.id == Order.store_id)
            .join(OrderItem, Order.id == OrderItem.order_id)
            .filter(OrderItem.product_id == product_id)
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
                "avg_discount": round(float(item[4]) if item[4] else 0, 2),
            }
            for item in results
        ]
    finally:
        db.close()