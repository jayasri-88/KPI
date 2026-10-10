"""
Database and PostGIS Integration Tests
Verifies live PostgreSQL engine connectivity, PostGIS functions, and schema constraints.
"""

from decimal import Decimal
from sqlalchemy import text
from app.models import Store, Product, Category, Order, Inventory


def test_postgresql_connection(db):
    """Verify live PostgreSQL server connection and current database name."""
    db_name = db.execute(text("SELECT current_database();")).scalar()
    pg_version = db.execute(text("SELECT version();")).scalar()
    assert db_name is not None
    assert "PostgreSQL" in pg_version


def test_postgis_spatial_extension(db):
    """Verify PostGIS extension is installed and responds to spatial function queries."""
    postgis_ver = db.execute(text("SELECT PostGIS_Version();")).scalar()
    assert postgis_ver is not None

    # Test spatial distance between Bangalore (77.5946, 12.9716) and Hyderabad (78.4867, 17.3850)
    query = text("""
        SELECT ST_Distance(
            ST_SetSRID(ST_MakePoint(77.5946, 12.9716), 4326)::geography,
            ST_SetSRID(ST_MakePoint(78.4867, 17.3850), 4326)::geography
        );
    """)
    distance_meters = db.execute(query).scalar()
    assert distance_meters is not None
    # Distance between Bangalore and Hyderabad is roughly 500km (450,000 - 550,000 meters)
    assert 450000 < distance_meters < 550000


def test_store_and_inventory_relationships(db):
    """Verify Store has valid PostGIS location geometry and linked inventory."""
    store = db.query(Store).filter(Store.is_active == True).first()
    assert store is not None
    assert store.location is not None
    assert float(store.latitude) > 0
    assert float(store.longitude) > 0

    # Verify inventory relationship
    assert len(store.inventory) > 0
    first_inv = store.inventory[0]
    assert first_inv.store_id == store.id
    assert first_inv.quantity_on_hand >= 0
    assert first_inv.product is not None


def test_product_category_and_margin_constraints(db):
    """Verify products link to categories and obey financial constraints."""
    products = db.query(Product).limit(10).all()
    assert len(products) > 0
    for p in products:
        assert p.category is not None
        assert p.unit_price >= 0
        assert p.cost_price >= 0
        assert p.unit_price >= p.cost_price
