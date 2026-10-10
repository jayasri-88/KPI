import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any, Dict, Generic, List, Optional, TypeVar
from pydantic import BaseModel, ConfigDict, EmailStr, Field


# ============================================================================
# 0. COMMON & PAGINATION SCHEMAS
# ============================================================================
T = TypeVar("T")


class PaginationMeta(BaseModel):
    total: int = Field(..., description="Total matching items count in database")
    page: int = Field(..., description="Current page number (1-indexed)")
    size: int = Field(..., description="Items per page")
    pages: int = Field(..., description="Total available pages")


class PaginatedResponse(BaseModel, Generic[T]):
    items: List[T]
    total: int
    page: int
    size: int
    pages: int


# ============================================================================
# 1. AUTHENTICATION & USER SCHEMAS
# ============================================================================
class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    role: str = "analyst"
    is_active: bool = True
    is_superuser: bool = False
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int = 86400
    user: Optional[UserResponse] = None


class TokenData(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    role: Optional[str] = None


class UserCreate(BaseModel):
    email: EmailStr = Field(..., description="User corporate or personal email")
    username: str = Field(..., min_length=3, max_length=50, description="Login handle")
    password: str = Field(..., min_length=6, description="Plaintext secret password")
    full_name: Optional[str] = Field(None, max_length=255, description="Full name")
    role: Optional[str] = Field("analyst", description="Role: admin, analyst, or manager")


class UserLogin(BaseModel):
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., description="Password")


class LogoutResponse(BaseModel):
    message: str = "Successfully logged out"


class UserSchema(UserResponse):
    pass


# ============================================================================
# 2. CATEGORY SCHEMAS
# ============================================================================
class CategoryBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=200, description="Category name")
    code: str = Field(..., min_length=1, max_length=50, description="Unique category code")
    description: Optional[str] = Field(None, description="Category description")
    target_margin_pct: Decimal = Field(default=Decimal("25.00"), description="Target gross margin percentage")
    is_active: bool = Field(default=True, description="Active status")


class CategoryCreate(CategoryBase):
    pass


class CategoryUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=200)
    code: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = None
    target_margin_pct: Optional[Decimal] = None
    is_active: Optional[bool] = None


class CategoryResponse(CategoryBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
CategorySchema = CategoryResponse


# ============================================================================
# 3. STORE SCHEMAS
# ============================================================================
class StoreBase(BaseModel):
    store_code: str = Field(..., min_length=2, max_length=50, description="Store code e.g. STR-MUM-01")
    name: str = Field(..., min_length=2, max_length=300, description="Store commercial name")
    store_type: str = Field(..., description="Flagship, Mall Outlet, Express, Hypermarket")
    address: Optional[str] = None
    city: str = Field(..., min_length=1, max_length=200)
    state: str = Field(..., min_length=1, max_length=200)
    region: str = Field(..., min_length=1, max_length=100)
    postal_code: Optional[str] = None
    latitude: Decimal = Field(..., ge=-90, le=90, description="Latitude coordinate")
    longitude: Decimal = Field(..., ge=-180, le=180, description="Longitude coordinate")
    store_size_sqft: int = Field(default=5000, gt=0, description="Store area in sqft")
    target_monthly_sales: Decimal = Field(default=Decimal("1000000.00"), description="Monthly revenue target")
    is_active: bool = Field(default=True)


class StoreCreate(StoreBase):
    pass


class StoreUpdate(BaseModel):
    name: Optional[str] = None
    store_type: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    region: Optional[str] = None
    postal_code: Optional[str] = None
    latitude: Optional[Decimal] = None
    longitude: Optional[Decimal] = None
    store_size_sqft: Optional[int] = None
    target_monthly_sales: Optional[Decimal] = None
    is_active: Optional[bool] = None


class StoreResponse(StoreBase):
    id: uuid.UUID
    opened_at: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class StorePerformance(BaseModel):
    store_id: uuid.UUID
    store_code: str
    name: str
    city: str
    region: str
    store_type: str
    latitude: Decimal
    longitude: Decimal
    total_revenue: Decimal
    total_orders: int
    average_order_value: Decimal
    total_profit: Decimal
    profit_margin_pct: Decimal
    target_monthly_sales: Decimal
    target_achievement_pct: Decimal

    model_config = ConfigDict(from_attributes=True)


class StoreSpatialFeature(BaseModel):
    store_id: uuid.UUID
    store_code: str
    name: str
    store_type: str
    address: Optional[str] = None
    city: str
    state: str
    region: str
    postal_code: Optional[str] = None
    latitude: Decimal
    longitude: Decimal
    store_size_sqft: int
    target_monthly_sales: Decimal
    is_active: bool
    total_revenue: Decimal
    total_profit: Decimal
    total_orders: int
    average_order_value: Decimal
    profit_margin_pct: Decimal
    target_achievement_pct: Decimal
    sales_per_sqft: Decimal
    distance_km: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class RegionalPerformanceItem(BaseModel):
    region: str
    store_count: int
    total_revenue: Decimal
    total_profit: Decimal
    total_orders: int
    average_order_value: Decimal
    profit_margin_pct: Decimal
    target_achievement_pct: Decimal
    centroid_lat: Optional[float] = None
    centroid_lng: Optional[float] = None
    top_store_name: Optional[str] = None


# Backwards compatibility alias
StoreSchema = StoreResponse


# ============================================================================
# 4. PRODUCT SCHEMAS
# ============================================================================
class ProductBase(BaseModel):
    sku_code: str = Field(..., min_length=3, max_length=100, description="Product SKU code")
    product_name: str = Field(..., min_length=1, max_length=300, description="Product name")
    description: Optional[str] = None
    category_id: uuid.UUID = Field(..., description="Foreign key reference to Category")
    brand: str = Field(..., min_length=1, max_length=200, description="Brand name")
    unit_price: Decimal = Field(..., ge=0, description="Selling retail price")
    cost_price: Decimal = Field(..., ge=0, description="Cost of goods sold (COGS)")
    is_active: bool = Field(default=True)


class ProductCreate(ProductBase):
    pass


class ProductUpdate(BaseModel):
    sku_code: Optional[str] = None
    product_name: Optional[str] = None
    description: Optional[str] = None
    category_id: Optional[uuid.UUID] = None
    brand: Optional[str] = None
    unit_price: Optional[Decimal] = None
    cost_price: Optional[Decimal] = None
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: Optional[datetime] = None
    category_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
ProductSchema = ProductResponse


# ============================================================================
# 5. CUSTOMER SCHEMAS
# ============================================================================
class CustomerBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=150)
    last_name: str = Field(..., min_length=1, max_length=150)
    phone: Optional[str] = None
    segment: str = Field(default="Regular", description="VIP, Regular, New, At-Risk")
    city: Optional[str] = None
    state: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone: Optional[str] = None
    segment: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None


class CustomerResponse(CustomerBase):
    id: uuid.UUID
    total_spend: Decimal
    total_orders_count: int
    last_order_date: Optional[datetime] = None
    created_at: datetime
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
CustomerSchema = CustomerResponse


# ============================================================================
# 6. ORDER & ORDER ITEM SCHEMAS
# ============================================================================
class OrderItemBase(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    unit_cost: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_price: Decimal = Field(..., ge=0)


class OrderItemCreate(BaseModel):
    product_id: uuid.UUID
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    unit_cost: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)


class OrderItemResponse(OrderItemBase):
    id: uuid.UUID
    order_id: uuid.UUID
    created_at: datetime
    product_name: Optional[str] = None
    sku_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderBase(BaseModel):
    store_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    order_date: datetime
    status: str = Field(default="completed")
    channel: str = Field(default="In-Store")
    payment_method: str = Field(default="Credit Card")
    subtotal: Decimal = Field(..., ge=0)
    discount_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    tax_amount: Decimal = Field(default=Decimal("0.00"), ge=0)
    total_amount: Decimal = Field(..., ge=0)
    total_items: int = Field(default=0, ge=0)


class OrderCreate(BaseModel):
    store_id: uuid.UUID
    customer_id: Optional[uuid.UUID] = None
    order_date: Optional[datetime] = None
    channel: str = Field(default="In-Store")
    payment_method: str = Field(default="Credit Card")
    items: List[OrderItemCreate]


class OrderResponse(OrderBase):
    id: uuid.UUID
    order_number: str
    created_at: datetime
    updated_at: Optional[datetime] = None
    store_name: Optional[str] = None
    customer_name: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class OrderDetailResponse(OrderResponse):
    order_items: List[OrderItemResponse] = []


# Backwards compatibility alias
OrderSchema = OrderResponse
OrderItemSchema = OrderItemResponse


# ============================================================================
# 7. SALE SCHEMAS
# ============================================================================
class SaleBase(BaseModel):
    order_id: uuid.UUID
    store_id: uuid.UUID
    product_id: uuid.UUID
    sale_date: datetime
    channel: str = "In-Store"
    quantity: int = Field(..., gt=0)
    unit_price: Decimal = Field(..., ge=0)
    cost_price: Decimal = Field(..., ge=0)
    revenue: Decimal = Field(..., ge=0)
    cogs: Decimal = Field(..., ge=0)
    gross_profit: Decimal
    margin_pct: Decimal


class SaleResponse(SaleBase):
    id: uuid.UUID
    created_at: datetime
    store_name: Optional[str] = None
    product_name: Optional[str] = None
    sku_code: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class SalesSummary(BaseModel):
    date: datetime
    total_revenue: Decimal
    total_cogs: Decimal
    total_profit: Decimal
    margin_pct: Decimal
    total_orders: int
    total_quantity: int
    average_order_value: Decimal


class SalesTrendPoint(BaseModel):
    period: str  # YYYY-MM-DD or YYYY-MM or YYYY-Www
    revenue: Decimal
    profit: Decimal
    orders_count: int
    units_sold: int
    average_order_value: Decimal


class SalesTrendResponse(BaseModel):
    interval: str  # daily, weekly, monthly
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    total_revenue: Decimal
    total_profit: Decimal
    points: List[SalesTrendPoint]


# Backwards compatibility alias
SaleSchema = SaleResponse


# ============================================================================
# 8. INVENTORY SCHEMAS
# ============================================================================
class InventoryBase(BaseModel):
    store_id: uuid.UUID
    product_id: uuid.UUID
    quantity_on_hand: int = Field(..., ge=0)
    quantity_reserved: int = Field(default=0, ge=0)
    quantity_available: int = Field(..., ge=0)
    reorder_point: int = Field(default=15, ge=0)
    reorder_quantity: int = Field(default=50, gt=0)


class InventoryUpdate(BaseModel):
    quantity_on_hand: Optional[int] = Field(None, ge=0)
    quantity_reserved: Optional[int] = Field(None, ge=0)
    quantity_available: Optional[int] = Field(None, ge=0)
    reorder_point: Optional[int] = Field(None, ge=0)
    reorder_quantity: Optional[int] = Field(None, gt=0)


class InventoryResponse(InventoryBase):
    id: uuid.UUID
    last_restocked: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    store_name: Optional[str] = None
    product_name: Optional[str] = None
    sku_code: Optional[str] = None
    stock_status: str = "In Stock"  # In Stock, Low Stock, Out of Stock

    model_config = ConfigDict(from_attributes=True)


class InventoryAlertItem(BaseModel):
    inventory_id: uuid.UUID
    store_id: uuid.UUID
    store_name: str
    product_id: uuid.UUID
    product_name: str
    sku_code: str
    quantity_on_hand: int
    quantity_available: int
    reorder_point: int
    reorder_quantity: int
    deficit: int
    urgency: str  # Critical, Warning

    model_config = ConfigDict(from_attributes=True)


# Backwards compatibility alias
InventorySchema = InventoryResponse


# ============================================================================
# 9. DASHBOARD & KPI SCHEMAS
# ============================================================================
class TopProductItem(BaseModel):
    product_id: uuid.UUID
    sku_code: str
    product_name: str
    brand: str
    category_name: str
    units_sold: int
    revenue: Decimal
    profit: Decimal
    margin_pct: Decimal


class TopStoreItem(BaseModel):
    store_id: uuid.UUID
    store_code: str
    name: str
    city: str
    region: str
    revenue: Decimal
    profit: Decimal
    orders_count: int
    target_achievement_pct: Decimal


class CategoryRevenueItem(BaseModel):
    category_id: uuid.UUID
    category_name: str
    revenue: Decimal
    units_sold: int
    share_pct: Decimal


class RecentOrderItem(BaseModel):
    order_id: uuid.UUID
    order_number: str
    store_name: str
    customer_name: Optional[str] = None
    order_date: datetime
    total_amount: Decimal
    status: str


class DashboardOverviewResponse(BaseModel):
    # Core Executive KPIs
    total_revenue: Decimal
    total_profit: Decimal
    total_orders: int
    total_customers: int
    average_order_value: Decimal
    gross_margin_pct: Decimal

    # Growth Metrics (Comparison with previous period)
    revenue_growth_pct: Decimal
    profit_growth_pct: Decimal
    orders_growth_pct: Decimal

    # Breakdown components
    top_products: List[TopProductItem]
    top_stores: List[TopStoreItem]
    category_distribution: List[CategoryRevenueItem]
    recent_orders: List[RecentOrderItem]

    # Meta
    period: str = "All Time / Filtered"
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None


# Backwards compatibility alias
KPIOverview = DashboardOverviewResponse
TopProduct = TopProductItem
TopStore = TopStoreItem


# ============================================================================
# 11. ANALYTICS & MACHINE LEARNING SCHEMAS (Phase 8)
# ============================================================================
class SalesTrendPoint(BaseModel):
    date: str
    revenue: float
    profit: float
    orders: int
    ma_7: Optional[float] = None
    ma_30: Optional[float] = None


class DayOfWeekPattern(BaseModel):
    day_name: str
    day_idx: int
    avg_revenue: float
    avg_orders: float
    share_pct: float


class SalesTrendAnalyticsResponse(BaseModel):
    points: List[SalesTrendPoint]
    day_of_week_pattern: List[DayOfWeekPattern]
    total_revenue: float
    avg_daily_revenue: float
    peak_day: str
    peak_day_revenue: float
    volatility_std: float


class CategoryDemandItem(BaseModel):
    category_name: str
    category_code: str
    sku_count: int
    total_units_sold: int
    total_revenue: float
    total_profit: float
    avg_selling_price: float
    revenue_share_pct: float


class DemandAnalyticsResponse(BaseModel):
    categories: List[CategoryDemandItem]
    total_units_sold: int
    total_revenue: float
    top_category_name: str


class ProductPerformanceItem(BaseModel):
    product_id: uuid.UUID
    sku_code: str
    product_name: str
    brand: str
    category_name: str
    unit_price: float
    cost_price: float
    units_sold: int
    total_revenue: float
    total_profit: float
    margin_pct: float
    revenue_share_pct: float
    cumulative_revenue_pct: float
    pareto_class: str


class ProductPerformanceAnalyticsResponse(BaseModel):
    products: List[ProductPerformanceItem]
    total_skus_analyzed: int
    pareto_summary: Dict[str, int]


class ForecastDataPoint(BaseModel):
    date: str
    actual_sales: Optional[float] = None
    forecast_sales: Optional[float] = None
    lower_bound: Optional[float] = None
    upper_bound: Optional[float] = None
    is_forecast: bool = False


class ModelEvaluationMetrics(BaseModel):
    mae: float
    rmse: float
    mape: float
    wape: float
    r2: float


class SalesForecastResponse(BaseModel):
    model_name: str
    horizon_days: int
    store_id: Optional[str] = None
    trained_at: Optional[str] = None
    last_observed_date: Optional[str] = None
    evaluation_metrics: ModelEvaluationMetrics
    features_used: Dict[str, str]
    total_forecast_revenue: float
    avg_daily_forecast: float
    data: List[ForecastDataPoint]


# ============================================================================
# 12. AI RETAIL ANALYST AGENT SCHEMAS (Phase 9)
# ============================================================================
class AgentChatRequest(BaseModel):
    message: str = Field(
        ...,
        min_length=1,
        max_length=1000,
        description="User prompt or question to the retail analyst (max 1,000 characters to mitigate prompt injection)",
    )
    conversation_id: Optional[str] = Field(
        None,
        max_length=128,
        description="Optional conversation session ID to maintain history",
    )


class AgentToolExecution(BaseModel):
    tool: str
    output: Any


class AgentChatResponse(BaseModel):
    answer: str
    tools_used: List[str]
    data: List[Dict[str, Any]]
    conversation_id: str