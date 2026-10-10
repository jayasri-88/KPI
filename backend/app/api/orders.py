from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Order, OrderItem, Product, Store, Customer
from app.schemas import OrderSchema, OrderCreate, OrderItemSchema, OrderItemCreate


router = APIRouter(tags=["Orders"])


@router.get("/", response_model=list)
def list_orders(
    skip: int = 0,
    limit: int = 100,
    store_id: str = None,
    customer_id: str = None,
    status: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Order)
    if store_id:
        from sqlalchemy import UUID
        query = query.filter(Order.store_id == UUID(store_id))
    if customer_id:
        from sqlalchemy import UUID
        query = query.filter(Order.customer_id == UUID(customer_id))
    if status:
        query = query.filter(Order.status == status)
    
    orders = query.order_by(desc(Order.created_at)).offset(skip).limit(limit).all()
    return orders


@router.get("/{order_id}", response_model=OrderSchema)
def get_order(order_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    order = db.query(Order).filter(Order.id == UUID(order_id)).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")
    return order


@router.post("/", response_model=OrderSchema)
def create_order(order: OrderCreate, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    
    # Validate store exists if provided
    if order.store_id:
        store = db.query(Store).filter(Store.id == UUID(order.store_id)).first()
        if not store:
            raise HTTPException(status_code=404, detail="Store not found")
    
    # Validate customer exists if provided
    if order.customer_id:
        customer = db.query(Customer).filter(Customer.id == UUID(order.customer_id)).first()
        if not customer:
            raise HTTPException(status_code=404, detail="Customer not found")
    
    db_order = Order(
        order_number=order.order_number,
        store_id=UUID(order.store_id) if order.store_id else None,
        customer_id=UUID(order.customer_id) if order.customer_id else None,
        total_amount=order.total_amount,
        total_items=order.total_items,
        total_revenue=order.total_revenue,
        discount_amount=order.discount_amount,
        status=order.status,
        payment_method=order.payment_method,
    )
    db.add(db_order)
    db.commit()
    db.refresh(db_order)
    return db_order


@router.post("/{order_id}/items", response_model=OrderItemSchema)
def add_order_item(order_id: str, item: OrderItemCreate, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    
    db_order = db.query(Order).filter(Order.id == UUID(order_id)).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    # Validate product exists
    product = db.query(Product).filter(Product.id == UUID(item.product_id) if False else Product.sku_code == item.product_sku).first()
    # Try by sku_code since we might not have product_id
    product = db.query(Product).filter(Product.sku_code == item.product_sku).first()
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")
    
    # Calculate total price
    total_price = item.unit_price * item.quantity
    discount = total_price * (item.discount_percent / 100)
    final_total = total_price - discount
    
    db_item = OrderItem(
        order_id=UUID(order_id),
        product_id=product.id,
        retailer_id=item.retailer_id,
        product_sku=item.product_sku,
        product_name=item.product_name,
        category_name=item.category_name,
        quantity=item.quantity,
        unit_price=item.unit_price,
        total_price=final_total,
        discount_percent=item.discount_percent,
    )
    db.add(db_item)
    
    # Update order totals
    db_order.total_items += item.quantity
    db_order.total_revenue += final_total
    db_order.discount_amount += discount
    
    db.commit()
    db.refresh(db_item)
    return db_item


@router.delete("/{order_id}/items/{item_id}", response_model=dict)
def remove_order_item(order_id: str, item_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    
    db_order = db.query(Order).filter(Order.id == UUID(order_id)).first()
    if not db_order:
        raise HTTPException(status_code=404, detail="Order not found")
    
    db_item = db.query(OrderItem).filter(OrderItem.id == UUID(item_id)).first()
    if not db_item:
        raise HTTPException(status_code=404, detail="Order item not found")
    
    # Recalculate order totals (simple approach - subtract item values)
    db_order.total_items -= db_item.quantity
    db_order.total_revenue -= db_item.total_price
    db_order.discount_amount -= db_item.discount_percent if hasattr(db_item, 'discount_percent') else 0
    
    db.delete(db_item)
    db.commit()
    return {"message": "Order item removed successfully"}