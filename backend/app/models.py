from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.sql import func

from app.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(100), unique=True, nullable=False, index=True)
    full_name = Column(String(255))
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    is_superuser = Column(Boolean, default=False, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("ix_users_email", email),
        Index("ix_users_username", username),
    )


class Category(Base):
    __tablename__ = "categories"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    name = Column(String(200), unique=True, nullable=False, index=True)
    description = Column(Text)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    products = relationship("Product", back_populates="category", cascade="all")


class Product(Base):
    __tablename__ = "products"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    sku_code = Column(String(100), unique=True, nullable=False, index=True)
    product_name = Column(String(300), nullable=False)
    description = Column(Text)
    category_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("categories.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    brand = Column(String(200))
    unit_price = Column(Float, nullable=False)
    cost_price = Column(Float, nullable=False)
    must_sell_flag = Column(Boolean, default=False, nullable=False)
    launch_date = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    category = relationship("Category", back_populates="products")
    order_items = relationship("OrderItem", back_populates="product", cascade="all")
    inventory = relationship("Inventory", back_populates="product", cascade="all")

    __table_args__ = (
        Index("ix_products_sku", sku_code),
        Index("ix_products_category_id", category_id),
    )


class Store(Base):
    __tablename__ = "stores"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    retailer_id = Column(Integer, unique=True, nullable=False, index=True)
    retailer_name = Column(String(300), nullable=False)
    store_type = Column(String(100), nullable=False)
    city = Column(String(200), nullable=False)
    state = Column(String(200), nullable=False)
    region = Column(String(100), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    prosperity_index = Column(Float, nullable=False)
    premiumness_index = Column(Float, nullable=False)
    store_size_sqft = Column(Integer, nullable=False)
    location = Column(
        "Geometry",
        nullable=False,
    )
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    orders = relationship("Order", back_populates="store", cascade="all")
    inventory = relationship("Inventory", back_populates="store", cascade="all")

    __table_args__ = (
        Index("ix_stores_retailer_id", retailer_id),
        Index("ix_stores_region", region),
    )


class Customer(Base):
    __tablename__ = "customers"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    email = Column(String(255), unique=True, nullable=False, index=True)
    first_name = Column(String(150), nullable=False)
    last_name = Column(String(150), nullable=False)
    phone = Column(String(50))
    city = Column(String(200))
    state = Column(String(200))
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    orders = relationship("Order", back_populates="customer", cascade="all")

    __table_args__ = (
        Index("ix_customers_email", email),
        Index("ix_customers_first_name", first_name),
    )


class Order(Base):
    __tablename__ = "orders"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    order_number = Column(String(100), unique=True, nullable=False, index=True)
    store_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("stores.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    customer_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("customers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    total_amount = Column(Float, nullable=False)
    total_items = Column(Integer, nullable=False, default=0)
    total_revenue = Column(Float, nullable=False)
    discount_amount = Column(Float, nullable=False, default=0.0)
    status = Column(String(50), nullable=False, default="completed")
    payment_method = Column(String(50), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    store = relationship("Store", back_populates="orders")
    customer = relationship("Customer", back_populates="orders")
    order_items = relationship("OrderItem", back_populates="order", cascade="all")

    __table_args__ = (
        Index("ix_orders_store_id", store_id),
        Index("ix_orders_customer_id", customer_id),
        Index("ix_orders_order_number", order_number),
        Index("ix_orders_created_at", created_at),
    )


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    order_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    product_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    retailer_id = Column(Integer, nullable=False)
    product_sku = Column(String(100), nullable=False)
    product_name = Column(String(300), nullable=False)
    category_name = Column(String(200), nullable=True)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    total_price = Column(Float, nullable=False)
    discount_percent = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    order = relationship("Order", back_populates="order_items")
    product = relationship("Product", back_populates="order_items")

    __table_args__ = (
        Index("ix_order_items_order_id", order_id),
        Index("ix_order_items_product_id", product_id),
        Index("ix_order_items_retailer_id", retailer_id),
    )


class Sales(Base):
    __tablename__ = "sales"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    retailer_id = Column(Integer, nullable=False)
    product_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
    )
    date = Column(DateTime(timezone=True), nullable=False)
    channel = Column(String(50), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit_price = Column(Float, nullable=False)
    revenue = Column(Float, nullable=False)
    discount_percent = Column(Float, nullable=False, default=0.0)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    __table_args__ = (
        Index("ix_sales_retailer_id", retailer_id),
        Index("ix_sales_product_id", product_id),
        Index("ix_sales_date", date),
        Index("ix_sales_date_retailer", date, retailer_id),
    )


class Inventory(Base):
    __tablename__ = "inventory"

    id = Column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=func.gen_random_uuid(),
    )
    product_id = Column(
        PGUUID(as_uuid=True),
        ForeignKey("products.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    retailer_id = Column(Integer, nullable=False)
    quantity_on_hand = Column(Integer, nullable=False, default=0)
    quantity_reserved = Column(Integer, nullable=False, default=0)
    quantity_available = Column(Integer, nullable=False, default=0)
    reorder_point = Column(Integer, nullable=False, default=10)
    reorder_quantity = Column(Integer, nullable=False, default=20)
    last_restocked = Column(DateTime(timezone=True), nullable=True)
    last_updated = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    product = relationship("Product", back_populates="inventory")
    store = relationship("Store", back_populates="inventory", foreign_keys=[retailer_id])

    __table_args__ = (
        Index("ix_inventory_product_id", product_id),
        Index("ix_inventory_retailer_id", retailer_id),
        Index("ix_inventory_available", quantity_available),
        Index("ix_inventory_retailer_product", retailer_id, product_id),
        UniqueConstraint("product_id", "retailer_id", name="uq_inventory_product_retailer"),
    )