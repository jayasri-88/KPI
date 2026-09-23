"""Analytics service integration tests.

Every expected value below is calculated by hand from the fixture data,
independently of the service implementation. The fixtures intentionally
include multi-line orders, two months, two regions, two categories and a
discounted vs non-discounted line so that grouping, aggregation, distinct
order counting and field mapping are all exercised.
"""

from datetime import datetime, timezone

import pytest

from app.models import (
    Category,
    Customer,
    Order,
    OrderItem,
    Product,
    Sales,
    Store,
)
from app.services import analytics_service, dashboard_service

JAN = datetime(2026, 1, 15, 10, 0, tzinfo=timezone.utc)
JAN_LATE = datetime(2026, 1, 25, 10, 0, tzinfo=timezone.utc)
FEB = datetime(2026, 2, 10, 10, 0, tzinfo=timezone.utc)


def seed_analytics_data(session):
    """Deterministic fixture data:

    Orders (order_items are the revenue source):
      O1 (Jan, North/S1): 2x Cola @100 with 5% discount -> total_price 190.0
      O2 (Jan, South/S2): 1x Chips @50, no discount     -> total_price  50.0
      O3 (Feb, North/S1): 1x Cola @100 with 5% discount -> total_price  95.0

    Sales fact rows (independent of orders):
      Jan: 3x Cola, revenue 285.0
      Feb: 2x Chips, revenue 100.0
    """
    cat_beverages = Category(name="Beverages", description="Drinks")
    cat_snacks = Category(name="Snacks", description="Nibbles")
    session.add_all([cat_beverages, cat_snacks])
    session.flush()

    p_cola = Product(
        sku_code="SKU-001",
        product_name="Cola 500ml",
        category_id=cat_beverages.id,
        unit_price=100.0,
        cost_price=60.0,
    )
    p_chips = Product(
        sku_code="SKU-002",
        product_name="Chips 100g",
        category_id=cat_snacks.id,
        unit_price=50.0,
        cost_price=30.0,
    )
    session.add_all([p_cola, p_chips])
    session.flush()

    store_north = Store(
        retailer_id=101,
        retailer_name="Mart One",
        store_type="hypermarket",
        city="Alpha City",
        state="Alpha State",
        region="North",
        latitude=12.9,
        longitude=77.5,
        prosperity_index=0.8,
        premiumness_index=0.7,
        store_size_sqft=5000,
        location="loc-north",
    )
    store_south = Store(
        retailer_id=102,
        retailer_name="Mart Two",
        store_type="supermarket",
        city="Beta City",
        state="Beta State",
        region="South",
        latitude=13.0,
        longitude=80.2,
        prosperity_index=0.6,
        premiumness_index=0.5,
        store_size_sqft=3000,
        location="loc-south",
    )
    session.add_all([store_north, store_south])
    session.flush()

    customer = Customer(
        email="alice@test.example",
        first_name="Alice",
        last_name="Lee",
    )
    session.add(customer)
    session.flush()

    o1 = Order(
        order_number="T-001",
        store_id=store_north.id,
        customer_id=customer.id,
        total_amount=190.0,
        total_revenue=190.0,
        created_at=JAN,
    )
    o2 = Order(
        order_number="T-002",
        store_id=store_south.id,
        total_amount=50.0,
        total_revenue=50.0,
        created_at=JAN_LATE,
    )
    o3 = Order(
        order_number="T-003",
        store_id=store_north.id,
        total_amount=95.0,
        total_revenue=95.0,
        created_at=FEB,
    )
    session.add_all([o1, o2, o3])
    session.flush()

    session.add_all(
        [
            OrderItem(
                order_id=o1.id,
                product_id=p_cola.id,
                retailer_id=101,
                product_sku="SKU-001",
                product_name="Cola 500ml",
                category_name="Beverages",
                quantity=2,
                unit_price=100.0,
                total_price=190.0,
                discount_percent=5.0,
            ),
            OrderItem(
                order_id=o2.id,
                product_id=p_chips.id,
                retailer_id=102,
                product_sku="SKU-002",
                product_name="Chips 100g",
                category_name="Snacks",
                quantity=1,
                unit_price=50.0,
                total_price=50.0,
                discount_percent=0.0,
            ),
            OrderItem(
                order_id=o3.id,
                product_id=p_cola.id,
                retailer_id=101,
                product_sku="SKU-001",
                product_name="Cola 500ml",
                category_name="Beverages",
                quantity=1,
                unit_price=100.0,
                total_price=95.0,
                discount_percent=5.0,
            ),
        ]
    )

    session.add_all(
        [
            Sales(
                retailer_id=101,
                product_id=p_cola.id,
                date=datetime(2026, 1, 20, tzinfo=timezone.utc),
                channel="in_store",
                quantity=3,
                unit_price=100.0,
                revenue=285.0,
                discount_percent=5.0,
            ),
            Sales(
                retailer_id=102,
                product_id=p_chips.id,
                date=datetime(2026, 2, 5, tzinfo=timezone.utc),
                channel="online",
                quantity=2,
                unit_price=50.0,
                revenue=100.0,
                discount_percent=0.0,
            ),
        ]
    )
    session.commit()

    return {
        "cola_id": p_cola.id,
        "chips_id": p_chips.id,
    }

class TestSalesTrend:
    def test_monthly_grouping_and_aggregation(self, service_sessions, seeded):
        trend = analytics_service.get_sales_trend()

        # 285 = 3 x 100 less 5%; 100 = 2 x 50 with no discount
        assert trend == [
            {"month": "2026-01", "revenue": 285.0, "units": 3, "transactions": 1},
            {"month": "2026-02", "revenue": 100.0, "units": 2, "transactions": 1},
        ]


class TestDashboardOverview:
    def test_totals(self, service_sessions, seeded):
        overview = dashboard_service.get_dashboard_overview()

        # 190 + 50 + 95
        assert overview["total_revenue"] == 335.0
        # 2 + 1 + 1
        assert overview["total_units"] == 4
        assert overview["total_transactions"] == 3
        # (5 + 0 + 5) / 3
        assert overview["avg_discount"] == 3.33
        assert overview["total_products"] == 2
        assert overview["total_retailers"] == 2

    def test_top_category_and_region(self, service_sessions, seeded):
        overview = dashboard_service.get_dashboard_overview()

        # Beverages: 190 + 95 = 285; Snacks: 50
        assert overview["top_category"] == "Beverages"
        assert overview["top_category_revenue"] == 285.0
        # North: 190 + 95 = 285; South: 50
        assert overview["top_region"] == "North"
        assert overview["top_region_revenue"] == 285.0

    def test_monthly_sales_split_by_order_month(self, service_sessions, seeded):
        overview = dashboard_service.get_dashboard_overview()

        assert overview["monthly_sales"] == [
            # Jan: items of O1 (190) + O2 (50); 2 distinct orders; 3 units
            # net = 190*0.95 + 50 = 230.5; profit = 2*40 + 1*20 = 100
            {
                "month": "2026-01",
                "revenue": 240.0,
                "net_revenue": 230.5,
                "profit": 100.0,
                "transactions": 2,
                "units": 3,
                "aov": 120.0,
            },
            # Feb: item of O3 (95); 1 distinct order; 1 unit
            # net = 95*0.95 = 90.25; profit = 1*40 = 40
            {
                "month": "2026-02",
                "revenue": 95.0,
                "net_revenue": 90.25,
                "profit": 40.0,
                "transactions": 1,
                "units": 1,
                "aov": 95.0,
            },
        ]


class TestCategoryPerformance:
    def test_names_revenue_and_distinct_order_counts(self, service_sessions, seeded):
        result = analytics_service.get_category_performance()

        assert result == [
            # Beverages: 190 + 95 across 2 distinct orders; profit 3x40 = 120
            {
                "category": "Beverages",
                "revenue": 285.0,
                "units": 3,
                "transactions": 2,
                "profit": 120.0,
            },
            {
                "category": "Snacks",
                "revenue": 50.0,
                "units": 1,
                "transactions": 1,
                "profit": 20.0,
            },
        ]

    def test_orders_descending_by_revenue(self, service_sessions, seeded):
        revenues = [r["revenue"] for r in analytics_service.get_category_performance()]
        assert revenues == sorted(revenues, reverse=True)


class TestSkuPerformance:
    def test_field_mapping(self, service_sessions, seeded):
        result = analytics_service.get_sku_performance()

        assert len(result) == 2
        cola = next(r for r in result if r["sku_code"] == "SKU-001")
        chips = next(r for r in result if r["sku_code"] == "SKU-002")

        assert cola["product_name"] == "Cola 500ml"
        assert cola["category"] == "Beverages"  # name, not a UUID string
        assert cola["units"] == 3  # 2 + 1
        assert cola["revenue"] == 285.0  # 190 + 95
        assert cola["avg_discount"] == 5.0  # (5 + 5) / 2
        assert cola["transactions"] == 2  # distinct orders O1, O3
        assert cola["product_id"] == str(seeded["cola_id"])

        assert chips["category"] == "Snacks"
        assert chips["units"] == 1
        assert chips["revenue"] == 50.0
        assert chips["avg_discount"] == 0.0
        assert chips["transactions"] == 1

        # profit: cola 3x(100-60)=120; chips 1x(50-30)=20
        assert cola["profit"] == 120.0
        assert chips["profit"] == 20.0

    def test_ordered_by_revenue_desc(self, service_sessions, seeded):
        result = analytics_service.get_sku_performance()
        assert result[0]["sku_code"] == "SKU-001"
        assert result[1]["sku_code"] == "SKU-002"


class TestRegionPerformance:
    def test_region_aggregates_and_retailer_count(self, service_sessions, seeded):
        result = analytics_service.get_region_performance()

        assert result == [
            {
                "region": "North",
                "revenue": 285.0,
                "units": 3,
                "transactions": 2,
                "retailer_count": 1,  # only S1 in North placed orders
            },
            {
                "region": "South",
                "revenue": 50.0,
                "units": 1,
                "transactions": 1,
                "retailer_count": 1,
            },
        ]


class TestEmptyDatabase:
    def test_zeroed_and_stable_responses(self, service_sessions, clean_tables):
        overview = dashboard_service.get_dashboard_overview()
        assert overview["total_revenue"] == 0.0
        assert overview["total_transactions"] == 0
        assert overview["monthly_sales"] == []
        assert overview["top_category"] == "N/A"

        assert analytics_service.get_sales_trend() == []
        assert analytics_service.get_category_performance() == []
        assert analytics_service.get_sku_performance() == []
        assert analytics_service.get_region_performance() == []
