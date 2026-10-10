import math
import uuid
from datetime import datetime, timezone
from typing import List, Optional
from sqlalchemy import func, desc, or_
from sqlalchemy.orm import Session, joinedload

from app.core.security import escape_like
from app.models import Inventory, Product, Store
from app.schemas import InventoryAlertItem, InventoryResponse, InventoryUpdate, PaginatedResponse


def get_inventory(
    db: Session,
    page: int = 1,
    size: int = 20,
    store_id: Optional[uuid.UUID] = None,
    product_id: Optional[uuid.UUID] = None,
    stock_status: Optional[str] = None,
    search: Optional[str] = None,
) -> PaginatedResponse[InventoryResponse]:
    query = (
        db.query(Inventory)
        .options(
            joinedload(Inventory.store),
            joinedload(Inventory.product),
        )
    )

    if store_id:
        query = query.filter(Inventory.store_id == store_id)
    if product_id:
        query = query.filter(Inventory.product_id == product_id)
    if search:
        s = f"%{escape_like(search.strip().lower())}%"
        query = (
            query.join(Store, Inventory.store_id == Store.id)
            .join(Product, Inventory.product_id == Product.id)
            .filter(
                or_(
                    func.lower(Product.product_name).like(s),
                    func.lower(Product.sku_code).like(s),
                    func.lower(Store.name).like(s),
                )
            )
        )

    if stock_status:
        st = stock_status.strip().lower()
        if st in ["out of stock", "out"]:
            query = query.filter(Inventory.quantity_available <= 0)
        elif st in ["low stock", "low"]:
            query = query.filter(
                Inventory.quantity_available > 0,
                Inventory.quantity_available <= Inventory.reorder_point,
            )
        elif st in ["in stock", "normal"]:
            query = query.filter(Inventory.quantity_available > Inventory.reorder_point)

    total = query.count()
    pages = math.ceil(total / size) if total > 0 else 1
    offset = (page - 1) * size

    inv_records = (
        query.order_by(Inventory.quantity_available.asc())
        .offset(offset)
        .limit(size)
        .all()
    )

    items: List[InventoryResponse] = []
    for inv in inv_records:
        resp = InventoryResponse.model_validate(inv)
        resp.store_name = inv.store.name if inv.store else None
        resp.product_name = inv.product.product_name if inv.product else None
        resp.sku_code = inv.product.sku_code if inv.product else None

        if inv.quantity_available <= 0:
            resp.stock_status = "Out of Stock"
        elif inv.quantity_available <= inv.reorder_point:
            resp.stock_status = "Low Stock"
        else:
            resp.stock_status = "In Stock"

        items.append(resp)

    return PaginatedResponse[InventoryResponse](
        items=items,
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_inventory_alerts(
    db: Session,
    store_id: Optional[uuid.UUID] = None,
) -> List[InventoryAlertItem]:
    """
    Identifies inventory positions breaching reorder thresholds.
    """
    query = (
        db.query(Inventory)
        .options(
            joinedload(Inventory.store),
            joinedload(Inventory.product),
        )
        .filter(Inventory.quantity_available <= Inventory.reorder_point)
    )

    if store_id:
        query = query.filter(Inventory.store_id == store_id)

    alerts_rows = query.order_by(Inventory.quantity_available.asc()).all()

    alerts: List[InventoryAlertItem] = []
    for inv in alerts_rows:
        deficit = max(0, inv.reorder_point - inv.quantity_available)
        urgency = "Critical" if inv.quantity_available <= 0 else "Warning"

        alerts.append(
            InventoryAlertItem(
                inventory_id=inv.id,
                store_id=inv.store_id,
                store_name=inv.store.name,
                product_id=inv.product_id,
                product_name=inv.product.product_name,
                sku_code=inv.product.sku_code,
                quantity_on_hand=inv.quantity_on_hand,
                quantity_available=inv.quantity_available,
                reorder_point=inv.reorder_point,
                reorder_quantity=inv.reorder_quantity,
                deficit=deficit,
                urgency=urgency,
            )
        )

    return alerts


def update_inventory(
    db: Session,
    inventory_id: uuid.UUID,
    inv_in: InventoryUpdate,
) -> Optional[Inventory]:
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        return None

    update_data = inv_in.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(inv, field, value)

    # Recompute available = on_hand - reserved
    inv.quantity_available = max(0, inv.quantity_on_hand - inv.quantity_reserved)
    inv.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(inv)

    try:
        from app.core.cache import cache_manager
        cache_manager.invalidate_dashboard_kpis()
    except Exception:
        pass

    return inv


def restock_inventory(
    db: Session,
    inventory_id: uuid.UUID,
    quantity_added: int,
) -> Optional[Inventory]:
    inv = db.query(Inventory).filter(Inventory.id == inventory_id).first()
    if not inv:
        return None

    inv.quantity_on_hand += quantity_added
    inv.quantity_available = max(0, inv.quantity_on_hand - inv.quantity_reserved)
    inv.last_restocked = datetime.now(timezone.utc)
    inv.updated_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(inv)

    try:
        from app.core.cache import cache_manager
        cache_manager.invalidate_dashboard_kpis()
    except Exception:
        pass

    return inv