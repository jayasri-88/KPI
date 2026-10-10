import uuid
from decimal import Decimal
from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    CheckConstraint,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func
from geoalchemy2 import Geometry

from app.database import Base


# ============================================================================
# 1. USER MODEL (Authentication & Authorization)
# ============================================================================
class User(Base):
    __tablename__ = "users"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255), nullable=True)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(50), nullable=False, default="analyst")  # admin, analyst, manager
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_users_email_active", email, is_active),
    )


# ============================================================================
# 2. CATEGORY MODEL
# ============================================================================
class Category(Base):
    __tablename__ = "categories"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    name = Column(String(200), unique=True, nullable=False, index=True)
    code = Column(String(50), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    target_margin_pct = Column(Numeric(5, 2), nullable=False, default=25.00)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    products = relationship("Product", back_populates="category", cascade="all, delete-orphan")


# ============================================================================
# 3. STORE MODEL (With PostGIS Spatial Geometry)
# ============================================================================
class Store(Base):
    __tablename__ = "stores"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    store_code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(300), nullable=False)
    store_type = Column(String(100), nullable=False)  # Flagship, Mall Outlet, Express, Hypermarket
    address = Column(String(500), nullable=True)
    city = Column(String(200), nullable=False, index=True)
    state = Column(String(200), nullable=False, index=True)
    region = Column(String(100), nullable=False, index=True)  # North, South, West, East
    postal_code = Column(String(20), nullable=True)

    # Coordinates & Spatial Column
    latitude = Column(Numeric(9, 6), nullable=False)
    longitude = Column(Numeric(9, 6), nullable=False)
    location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)

    # Business attributes
    store_size_sqft = Column(Integer, nullable=False, default=5000)
    target_monthly_sales = Column(Numeric(12, 2), nullable=False, default=1000000.00)
    is_active = Column(Boolean, default=True, nullable=False)
    opened_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    orders = relationship("Order", back_populates="store", cascade="all, delete-orphan")
    inventory = relationship("Inventory", back_populates="store", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="store", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_stores_city_region", city, region),
        Index("ix_stores_location", location, postgresql_using="gist"),
        CheckConstraint("latitude BETWEEN -90 AND 90", name="chk_store_latitude"),
        CheckConstraint("longitude BETWEEN -180 AND 180", name="chk_store_longitude"),
    )


# ============================================================================
# 4. PRODUCT MODEL
# ============================================================================
class Product(Base):
    __tablename__ = "products"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    sku_code = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(300), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    brand = Column(String(200), nullable=False, index=True)
    unit_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product")
    inventory = relationship("Inventory", back_populates="product", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="product")

    __table_args__ = (
        CheckConstraint("unit_price >= 0", name="chk_product_unit_price"),
        CheckConstraint("cost_price >= 0", name="chk_product_cost_price"),
        CheckConstraint("unit_price >= cost_price", name="chk_product_selling_margin"),
        Index("ix_products_brand_category", brand, category_id),
    )


# ============================================================================
# 5. CUSTOMER MODEL
# ============================================================================
class Customer(Base):
    __tablename__ = "customers"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    phone = Column(String(50), nullable=True)
    segment = Column(String(50), nullable=False, default="Regular")  # VIP, Regular, New, At-Risk
    city = Column(String(200), nullable=True, index=True)
    state = Column(String(200), nullable=True)
    total_spend = Column(Numeric(14, 2), nullable=False, default=0.00)
    total_orders_count = Column(Integer, nullable=False, default=0)
    last_order_date = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    orders = relationship("Order", back_populates="customer", cascade="all, delete-orphan")

    __table_args__ = (
        Index("ix_customers_segment_city", segment, city),
    )


# ============================================================================
# 6. ORDER MODEL
# ============================================================================
class Order(Base):
    __tablename__ = "orders"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    store_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    customer_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    order_date = Column(DateTime(timezone=True), nullable=False, index=True)
    status = Column(String(50), nullable=False, default="completed")  # completed, returned, cancelled
    channel = Column(String(50), nullable=False, default="In-Store")  # In-Store, Online, Express Delivery
    payment_method = Column(String(50), nullable=False, default="Credit Card")  # Card, Cash, UPI, NetBanking

    # Financial breakdown (Decimals)
    subtotal = Column(Numeric(14, 2), nullable=False, default=0.00)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    tax_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    total_amount = Column(Numeric(14, 2), nullable=False, default=0.00)  # subtotal - discount + tax
    total_items = Column(Integer, nullable=False, default=0)

    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    store = relationship("Store", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")
    sales = relationship("Sale", back_populates="order", cascade="all, delete-orphan")

    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_order_total_amount"),
        CheckConstraint("subtotal >= 0", name="chk_order_subtotal"),
        Index("ix_orders_store_date", store_id, order_date),
        Index("ix_orders_customer_date", customer_id, order_date),
        Index("ix_orders_status_date", status, order_date),
    )


# ============================================================================
# 7. ORDER ITEM MODEL
# ============================================================================
class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    order_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    unit_cost = Column(Numeric(12, 2), nullable=False)
    discount_amount = Column(Numeric(12, 2), nullable=False, default=0.00)
    total_price = Column(Numeric(14, 2), nullable=False)  # (quantity * unit_price) - discount_amount
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_order_item_quantity"),
        CheckConstraint("unit_price >= 0", name="chk_order_item_unit_price"),
        CheckConstraint("total_price >= 0", name="chk_order_item_total_price"),
        Index("ix_order_items_product_order", product_id, order_id),
    )


# ============================================================================
# 8. SALE MODEL (Consolidated Financial Analytics Entity)
# ============================================================================
class Sale(Base):
    __tablename__ = "sales"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    order_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    store_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
    )
    sale_date = Column(DateTime(timezone=True), nullable=False, index=True)
    channel = Column(String(50), nullable=False, default="In-Store")
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Numeric(12, 2), nullable=False)
    cost_price = Column(Numeric(12, 2), nullable=False)
    revenue = Column(Numeric(14, 2), nullable=False)       # net revenue earned
    cogs = Column(Numeric(14, 2), nullable=False)          # cost of goods sold = quantity * cost_price
    gross_profit = Column(Numeric(14, 2), nullable=False)  # revenue - cogs
    margin_pct = Column(Numeric(6, 2), nullable=False)     # (gross_profit / revenue) * 100
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    order = relationship("Order", back_populates="sales")
    store = relationship("Store", back_populates="sales")
    product = relationship("Product", back_populates="sales")

    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_sale_quantity"),
        Index("ix_sales_date_store", sale_date, store_id),
        Index("ix_sales_date_product", sale_date, product_id),
        Index("ix_sales_store_product_date", store_id, product_id, sale_date),
    )


# Backward-compatibility alias
Sales = Sale


# ============================================================================
# 9. INVENTORY MODEL (Multi-Store Stock Tracking)
# ============================================================================
class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=func.gen_random_uuid(),
    )
    store_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_available = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=15)
    reorder_quantity = Column(Integer, nullable=False, default=50)
    last_restocked = Column(DateTime(timezone=True), nullable=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    # Relationships
    store = relationship("Store", back_populates="inventory")
    product = relationship("Product", back_populates="inventory")

    __table_args__ = (
        UniqueConstraint("store_id", "product_id", name="uq_inventory_store_product"),
        CheckConstraint("quantity_on_hand >= 0", name="chk_inv_qty_on_hand"),
        CheckConstraint("quantity_reserved >= 0", name="chk_inv_qty_reserved"),
        CheckConstraint("quantity_available >= 0", name="chk_inv_qty_available"),
        Index("ix_inventory_store_product", store_id, product_id),
        Index("ix_inventory_stock_alert", store_id, quantity_available, reorder_point),
    )