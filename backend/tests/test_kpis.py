"""KPI correctness tests.

Builds on the fixture data from test_analytics (3 completed orders,
revenue 335.0) and adds two adversarial orders:

  O4: status='cancelled', Feb, 2x Cola @100 (gross 200)  -> must be
      excluded from every order-derived KPI
  O5: status='completed' but has NO order_items          -> must NOT count
      as a transaction (transactions = orders with >= 1 line)

Every expected value is calculated by hand from the fixture definition.
"""

import pytest

from app.models import Order, OrderItem, Product, Store
from app.services import analytics_service, dashboard_service
from test_analytics import FEB, JAN, JAN_LATE, seed_analytics_data


@pytest.fixture()
def kpi_seeded(db_session, clean_tables):
    """Standard fixture + cancelled order + completed line-less order."""
    ids = seed_analytics_data(db_session)

    store_north = db_session.query(Store).filter_by(retailer_id=101).one()
    cola = db_session.query(Product).filter_by(sku_code="SKU-001").one()

    # Cancelled Feb order: would add 200 revenue / 2 units if not excluded.
    o4 = Order(
        order_number="T-004",
        store_id=store_north.id,
        total_amount=200.0,
        total_revenue=190.0,
        discount_amount=10.0,
        status="cancelled",
        created_at=FEB,
    )
    db_session.add(o4)
    db_session.flush()
    db_session.add(
        OrderItem(
            order_id=o4.id,
            product_id=cola.id,
            retailer_id=101,
            product_sku="SKU-001",
            product_name="Cola 500ml",
            category_name="Beverages",
            quantity=2,
            unit_price=100.0,
            total_price=200.0,
            discount_percent=5.0,
        )
    )

    # Completed order with no lines: must not count as a transaction.
    db_session.add(
        Order(
            order_number="T-005",
            store_id=store_north.id,
            total_amount=0.0,
            total_revenue=0.0,
            status="completed",
            created_at=FEB,
        )
    )
    db_session.commit()
    return ids


class TestCancelledOrderExclusion:
    def test_excluded_from_all_core_kpis(self, service_sessions, kpi_seeded):
        o = dashboard_service.get_dashboard_overview()

        # Without exclusion these would be 535.0 / 6 / 4 / 280.0.
        assert o["total_revenue"] == 335.0
        assert o["total_units"] == 4
        assert o["total_transactions"] == 3  # O4 cancelled, O5 has no lines
        assert o["total_profit"] == 140.0
        assert o["avg_discount"] == 3.33  # line-weighted mean of (5, 0, 5)

    def test_lineless_completed_order_is_not_a_transaction(
        self, service_sessions, kpi_seeded
    ):
        o = dashboard_service.get_dashboard_overview()
        # 3 revenue-bearing orders (O1..O3), not 4 (O5) or 5.
        assert o["total_transactions"] == 3
        # AOV = 335 / 3
        assert o["avg_order_value"] == 111.67

    def test_excluded_from_monthly_series(self, service_sessions, kpi_seeded):
        o = dashboard_service.get_dashboard_overview()
        feb = next(m for m in o["monthly_sales"] if m["month"] == "2026-02")
        # Feb would include the cancelled 200.0 without exclusion.
        assert feb["revenue"] == 95.0
        assert feb["profit"] == 40.0
        assert feb["transactions"] == 1
        assert feb["aov"] == 95.0

    def test_excluded_from_category_and_region(self, service_sessions, kpi_seeded):
        cats = analytics_service.get_category_performance()
        bev = next(c for c in cats if c["category"] == "Beverages")
        assert bev["revenue"] == 285.0
        assert bev["transactions"] == 2

        regions = analytics_service.get_region_performance()
        north = next(r for r in regions if r["region"] == "North")
        assert north["revenue"] == 285.0

        skus = analytics_service.get_sku_performance()
        cola = next(s for s in skus if s["sku_code"] == "SKU-001")
        assert cola["revenue"] == 285.0
        assert cola["units"] == 3
        assert cola["transactions"] == 2


class TestAov:
    def test_aov_is_revenue_over_transactions(self, service_sessions, seeded):
        o = dashboard_service.get_dashboard_overview()
        # 335.0 / 3 = 111.666... -> 111.67
        assert o["avg_order_value"] == 111.67

    def test_aov_per_month(self, service_sessions, seeded):
        o = dashboard_service.get_dashboard_overview()
        by_month = {m["month"]: m for m in o["monthly_sales"]}
        assert by_month["2026-01"]["aov"] == 120.0  # 240 / 2
        assert by_month["2026-02"]["aov"] == 95.0  # 95 / 1


class TestProfit:
    def test_profit_uses_product_cost(self, service_sessions, seeded):
        o = dashboard_service.get_dashboard_overview()
        # Cola: 3 x (100 - 60) = 120; Chips: 1 x (50 - 30) = 20
        assert o["total_profit"] == 140.0
        # 140 / 335 = 41.79%
        assert o["profit_margin"] == 41.79

    def test_profit_guard_zero_cost(self, service_sessions, clean_tables, db_session):
        """A zero-cost product must not crash margin math (div-by-zero guard
        lives in cost subtraction; margin guard is on revenue)."""
        from datetime import datetime, timezone

        cat = __import__("app.models", fromlist=["Category"]).Category(name="C")
        p = Product(
            sku_code="SKU-FREE",
            product_name="Free item",
            category_id=cat.id,
            unit_price=25.0,
            cost_price=0.0,
        )
        s = Store(
            retailer_id=201,
            retailer_name="S",
            store_type="kirana",
            city="X",
            state="Y",
            region="R",
            latitude=1.0,
            longitude=1.0,
            prosperity_index=0.5,
            premiumness_index=0.5,
            store_size_sqft=100,
            location="POINT(1 1)",
        )
        db_session.add_all([cat, p, s])
        db_session.flush()
        o = Order(
            order_number="T-FREE",
            store_id=s.id,
            total_amount=25.0,
            total_revenue=25.0,
            created_at=datetime(2026, 3, 1, tzinfo=timezone.utc),
        )
        db_session.add(o)
        db_session.flush()
        db_session.add(
            OrderItem(
                order_id=o.id,
                product_id=p.id,
                retailer_id=201,
                product_sku="SKU-FREE",
                product_name="Free item",
                category_name="C",
                quantity=1,
                unit_price=25.0,
                total_price=25.0,
                discount_percent=0.0,
            )
        )
        db_session.commit()

        result = analytics_service.get_sku_performance()
        assert result[0]["profit"] == 25.0  # 1 x (25 - 0)


class TestGrowth:
    def test_growth_compares_equivalent_months(self, service_sessions, kpi_seeded):
        o = dashboard_service.get_dashboard_overview()
        # revenue: (95 - 240) / 240 = -60.42%
        assert o["revenue_growth"] == -60.42
        # profit: (40 - 100) / 100 = -60.0%
        assert o["profit_growth"] == -60.0

    def test_growth_none_for_single_month(
        self, service_sessions, clean_tables, db_session
    ):
        """Only one month of data -> growth must be None, not 0 or a crash."""
        from datetime import datetime, timezone

        cat = __import__("app.models", fromlist=["Category"]).Category(name="C")
        p = Product(
            sku_code="SKU-001",
            product_name="P",
            category_id=cat.id,
            unit_price=10.0,
            cost_price=5.0,
        )
        s = Store(
            retailer_id=301,
            retailer_name="S",
            store_type="kirana",
            city="X",
            state="Y",
            region="R",
            latitude=1.0,
            longitude=1.0,
            prosperity_index=0.5,
            premiumness_index=0.5,
            store_size_sqft=100,
            location="POINT(1 1)",
        )
        db_session.add_all([cat, p, s])
        db_session.flush()
        o = Order(
            order_number="T-ONLY",
            store_id=s.id,
            total_amount=10.0,
            total_revenue=10.0,
            created_at=datetime(2026, 5, 1, tzinfo=timezone.utc),
        )
        db_session.add(o)
        db_session.flush()
        db_session.add(
            OrderItem(
                order_id=o.id,
                product_id=p.id,
                retailer_id=301,
                product_sku="SKU-001",
                product_name="P",
                category_name="C",
                quantity=1,
                unit_price=10.0,
                total_price=10.0,
                discount_percent=0.0,
            )
        )
        db_session.commit()

        o = dashboard_service.get_dashboard_overview()
        assert o["revenue_growth"] is None
        assert o["profit_growth"] is None


class TestContribution:
    def test_category_and_region_shares(self, service_sessions, seeded):
        o = dashboard_service.get_dashboard_overview()
        # 285 / 335 = 85.07%
        assert o["top_category_share"] == 85.07
        assert o["top_region_share"] == 85.07

    def test_shares_none_without_revenue(self, service_sessions, clean_tables):
        o = dashboard_service.get_dashboard_overview()
        assert o["top_category_share"] is None
        assert o["top_region_share"] is None
        assert o["avg_order_value"] is None
        assert o["profit_margin"] is None
