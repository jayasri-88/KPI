from pydantic import BaseModel, Field, EmailStr
from typing import Optional, List
from datetime import datetime
from sqlalchemy import UUID as SQLUUID


# --- Authentication Schemas ---

class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    email: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=100, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="Password")


class UserInDB(BaseModel):
    id: str = Field(..., alias="_id")
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    hashed_password: str
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"arbitrary_types_allowed": True}


# --- User Schemas ---

class UserSchema(BaseModel):
    id: str = Field(alias="id")
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    is_active: bool
    is_superuser: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Category Schemas ---

class CategorySchema(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# --- Product Schemas ---

class ProductSchema(BaseModel):
    id: str
    sku_code: str
    product_name: str
    description: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    unit_price: float
    cost_price: float
    must_sell_flag: bool
    launch_date: Optional[datetime] = None
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProductCreate(BaseModel):
    sku_code: str = Field(..., min_length=3, description="Product SKU code")
    product_name: str = Field(..., min_length=1, description="Product name")
    description: Optional[str] = None
    category_id: Optional[str] = None
    brand: Optional[str] = None
    unit_price: float = Field(..., gt=0, description="Unit price")
    cost_price: float = Field(..., ge=0, description="Cost price")
    must_sell_flag: bool = Field(default=False, description="Must sell flag")
    launch_date: Optional[datetime] = None
    is_active: bool = Field(default=True, description="Is active")


# --- Store Schemas ---

class StoreSchema(BaseModel):
    id: str
    retailer_id: int
    retailer_name: str
    store_type: str
    city: str
    state: str
    region: str
    latitude: float
    longitude: float
    prosperity_index: float
    premiumness_index: float
    store_size_sqft: int
    location: str
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class StoreCreate(BaseModel):
    retailer_id: int = Field(..., gt=0, description="Retailer ID")
    retailer_name: str = Field(..., min_length=1, description="Retailer name")
    store_type: str = Field(..., description="Store type")
    city: str = Field(..., min_length=1, description="City")
    state: str = Field(..., min_length=1, description="State")
    region: str = Field(..., min_length=1, description="Region")
    latitude: float = Field(..., description="Latitude")
    longitude: float = Field(..., description="Longitude")
    prosperity_index: float = Field(..., ge=0, le=1, description="Prosperity index")
    premiumness_index: float = Field(..., ge=0, le=1, description="Premiumness index")
    store_size_sqft: int = Field(..., gt=0, description="Store size in sq ft")


class StoreUpdate(BaseModel):
    retailer_name: Optional[str] = Field(None, min_length=1)
    store_type: Optional[str] = Field(None)
    city: Optional[str] = Field(None, min_length=1)
    state: Optional[str] = Field(None, min_length=1)
    region: Optional[str] = Field(None, min_length=1)
    latitude: Optional[float] = Field(None)
    longitude: Optional[float] = Field(None)
    prosperity_index: Optional[float] = Field(None, ge=0, le=1)
    premiumness_index: Optional[float] = Field(None, ge=0, le=1)
    store_size_sqft: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = Field(None)


# --- Customer Schemas ---

class CustomerSchema(BaseModel):
    id: str
    email: EmailStr
    first_name: str
    last_name: str
    phone: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class CustomerCreate(BaseModel):
    email: EmailStr = Field(..., description="Customer email")
    first_name: str = Field(..., min_length=1, description="First name")
    last_name: str = Field(..., min_length=1, description="Last name")
    phone: Optional[str] = Field(None, max_length=50, description="Phone number")
    city: Optional[str] = Field(None, max_length=200, description="City")
    state: Optional[str] = Field(None, max_length=200, description="State")


# --- Order Schemas ---

class OrderItemSchema(BaseModel):
    id: str
    product_sku: str
    product_name: str
    category_name: Optional[str] = None
    quantity: int
    unit_price: float
    total_price: float
    discount_percent: float
    created_at: datetime

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_sku: str = Field(..., min_length=1, description="Product SKU")
    product_name: str = Field(..., min_length=1, description="Product name")
    category_name: Optional[str] = Field(None, max_length=200, description="Category name")
    quantity: int = Field(..., gt=0, description="Quantity")
    unit_price: float = Field(..., gt=0, description="Unit price")
    discount_percent: float = Field(default=0.0, ge=0, le=100, description="Discount percent")


class OrderSchema(BaseModel):
    id: str
    order_number: str
    store_id: Optional[str] = None
    customer_id: Optional[str] = None
    total_amount: float
    total_items: int
    total_revenue: float
    discount_amount: float
    status: str
    payment_method: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class OrderCreate(BaseModel):
    order_number: str = Field(..., min_length=1, description="Order number")
    store_id: Optional[str] = Field(None, description="Store ID")
    customer_id: Optional[str] = Field(None, description="Customer ID")
    total_amount: float = Field(..., gt=0, description="Total amount")
    total_items: int = Field(default=0, ge=0, description="Total items")
    total_revenue: float = Field(..., gt=0, description="Total revenue")
    discount_amount: float = Field(default=0.0, ge=0, description="Discount amount")
    status: str = Field(default="completed", description="Order status")
    payment_method: Optional[str] = Field(None, max_length=50, description="Payment method")


# --- Sales Schemas ---

class SalesSummary(BaseModel):
    date: datetime
    total_revenue: float
    total_orders: int
    total_quantity: int
    average_order_value: float


class DailySales(BaseModel):
    date: datetime
    revenue: float
    orders: int
    quantity: int


# --- Inventory Schemas ---

class InventorySchema(BaseModel):
    id: str
    product_id: str
    retailer_id: int
    quantity_on_hand: int
    quantity_reserved: int
    quantity_available: int
    reorder_point: int
    reorder_quantity: int
    last_restocked: Optional[datetime] = None
    last_updated: datetime

    class Config:
        from_attributes = True


class InventoryUpdate(BaseModel):
    quantity_on_hand: int = Field(..., ge=0, description="Quantity on hand")
    quantity_reserved: int = Field(default=0, ge=0, description="Quantity reserved")
    reorder_point: int = Field(..., ge=0, description="Reorder point")
    reorder_quantity: int = Field(..., gt=0, description="Reorder quantity")


# --- Dashboard/KPI Schemas ---

class KPIOverview(BaseModel):
    total_revenue: float
    total_profit: float
    total_orders: int
    average_order_value: float
    total_customers: int
    revenue_growth: Optional[float] = None
    profit_growth: Optional[float] = None


class TopProduct(BaseModel):
    product_id: str
    product_name: str
    sku_code: str
    total_sales: float
    total_quantity: int


class TopStore(BaseModel):
    store_id: str
    retailer_name: str
    total_revenue: float
    total_orders: int


# --- Forecast Schemas ---

class ForecastPoint(BaseModel):
    date: datetime
    predicted_revenue: float
    lower_bound: float
    upper_bound: float


class ForecastResult(BaseModel):
    product_id: str
    product_name: str
    forecasts: List[ForecastPoint]


# --- Comparison Schemas ---

class StoreComparison(BaseModel):
    store_id: str
    retailer_name: str
    region: str
    total_revenue: float
    total_profit: float
    total_orders: int
    average_order_value: float


class PeriodComparison(BaseModel):
    period: str
    revenue: float
    profit: float
    orders: int
    growth_rate: Optional[float] = None


# --- Product Update Schema ---

class ProductUpdate(BaseModel):
    sku_code: Optional[str] = Field(None, min_length=3, description="Product SKU code")
    product_name: Optional[str] = Field(None, min_length=1, description="Product name")
    description: Optional[str] = Field(None, description="Product description")
    category_id: Optional[str] = Field(None, description="Category ID")
    brand: Optional[str] = Field(None, description="Brand name")
    unit_price: Optional[float] = Field(None, gt=0, description="Unit price")
    cost_price: Optional[float] = Field(None, ge=0, description="Cost price")
    must_sell_flag: Optional[bool] = Field(None, description="Must sell flag")
    launch_date: Optional[datetime] = Field(None, description="Launch date")
    is_active: Optional[bool] = Field(None, description="Is active")