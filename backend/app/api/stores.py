from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, asc

from app.database import get_db
from app.models import Store, User
from app.schemas import StoreSchema, StoreCreate, StoreUpdate

router = APIRouter(tags=["Stores"])


@router.get("/", response_model=list)
def list_stores(
    skip: int = 0,
    limit: int = 100,
    region: str = None,
    status: str = None,
    db: Session = Depends(get_db),
):
    query = db.query(Store)
    if region:
        query = query.filter(Store.region == region)
    if status:
        query = query.filter(Store.is_active == (status == "active"))
    
    stores = query.offset(skip).limit(limit).all()
    return stores


@router.get("/{store_id}", response_model=dict)
def get_store(store_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    store = db.query(Store).filter(Store.id == UUID(store_id)).first()
    if not store:
        raise HTTPException(status_code=404, detail="Store not found")
    return store


@router.post("/", response_model=dict)
def create_store(store: StoreCreate, db: Session = Depends(get_db)):
    db_store = Store(
        retailer_id=store.retailer_id,
        retailer_name=store.retailer_name,
        store_type=store.store_type,
        city=store.city,
        state=store.state,
        region=store.region,
        latitude=store.latitude,
        longitude=store.longitude,
        prosperity_index=store.prosperity_index,
        premiumness_index=store.premiumness_index,
        store_size_sqft=store.store_size_sqft,
        location=store.location,
    )
    db.add(db_store)
    db.commit()
    db.refresh(db_store)
    return {"message": "Store created successfully", "store_id": str(db_store.id)}


@router.put("/{store_id}", response_model=dict)
def update_store(store_id: str, store: StoreUpdate, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    db_store = db.query(Store).filter(Store.id == UUID(store_id)).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    update_data = store.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_store, key, value)
    
    db.commit()
    db.refresh(db_store)
    return {"message": "Store updated successfully"}


@router.delete("/{store_id}", response_model=dict)
def delete_store(store_id: str, db: Session = Depends(get_db)):
    from sqlalchemy import UUID
    db_store = db.query(Store).filter(Store.id == UUID(store_id)).first()
    if not db_store:
        raise HTTPException(status_code=404, detail="Store not found")
    
    db_store.is_active = False
    db.commit()
    return {"message": "Store deactivated successfully"}