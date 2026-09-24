from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.database import get_db
from app.models import Customer
from app.schemas import CustomerSchema, CustomerCreate


router = APIRouter(tags=["Customers"])


@router.get("/", response_model=list[CustomerSchema])
def list_customers(
    skip: int = 0,
    limit: int = 100,
    city: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Customer)
    if city:
        query = query.filter(Customer.city.ilike(f"%{city}%"))
    
    customers = query.offset(skip).limit(limit).all()
    return customers


@router.get("/{customer_id}", response_model=CustomerSchema)
def get_customer(customer_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    customer = db.query(Customer).filter(Customer.id == UUID(customer_id)).first()
    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    return customer


@router.post("/", response_model=CustomerSchema)
def create_customer(customer: CustomerCreate, db: Session = Depends(get_db)):
    # Check if customer already exists
    existing = db.query(Customer).filter(Customer.email == customer.email).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Customer with this email already exists",
        )
    
    db_customer = Customer(
        email=customer.email,
        first_name=customer.first_name,
        last_name=customer.last_name,
        phone=customer.phone,
        city=customer.city,
        state=customer.state,
    )
    db.add(db_customer)
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.put("/{customer_id}", response_model=CustomerSchema)
def update_customer(customer_id: str, customer_data: CustomerCreate, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    db_customer = db.query(Customer).filter(Customer.id == UUID(customer_id)).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    update_data = customer_data.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_customer, key, value)
    
    db.commit()
    db.refresh(db_customer)
    return db_customer


@router.delete("/{customer_id}", response_model=dict)
def delete_customer(customer_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    db_customer = db.query(Customer).filter(Customer.id == UUID(customer_id)).first()
    if not db_customer:
        raise HTTPException(status_code=404, detail="Customer not found")
    
    # Check if customer has orders
    from app.models import Order
    has_orders = db.query(Order).filter(Order.customer_id == UUID(customer_id)).first()
    if has_orders:
        raise HTTPException(
            status_code=400,
            detail="Cannot delete customer: has existing orders",
        )
    
    db.delete(db_customer)
    db.commit()
    return {"message": "Customer deleted successfully"}