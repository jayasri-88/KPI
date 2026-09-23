"""Idempotent PostgreSQL ingestion for the Retail KPI Intelligence Platform.

Reads the CSVs in ``data/`` and loads them into the application's
PostgreSQL database (the same DATABASE_URL the API uses), making PostgreSQL
the source of truth for retail business data.

Source files and their targets
------------------------------
products.csv            -> categories + products
retailers.csv           -> stores
sales_transactions.csv  -> sales (flat fact rows for trend analytics)
                        -> orders + order_items (each transaction becomes a
                           single-line order: order_number = SALE-<sale_id>,
                           line total_price = qty*unit_price GROSS, matching
                           the source's verified revenue convention;
                           discount_amount = gross - net; no customer
                           dimension exists in the source, so customer_id
                           stays NULL)
inventory.csv           -> inventory          (latest snapshot per
                                                (retailer_id, product_id);
                                                the model keeps current state
                                                only, UNIQUE per pair)
monthly_kpis.csv        -> intentionally NOT loaded: it is a pre-aggregated
                                                regional KPI cube. The API
                                                computes these numbers live
                                                from `sales`; storing them too
                                                would create a second,
                                                divergent copy of the truth.

Identity / idempotency strategy
-------------------------------
* Natural business keys from the source are mirrored into unique columns:
  stores.retailer_id (unique), products.sku_code (unique), sales.sale_id
  is stored implicitly by deterministic UUIDv5 of the source sale_id.
* UUIDs are generated with uuid5 (namespace + source business key), so the
  same source row always maps to the same database UUID across reruns.
* Every load is an UPSERT (insert or update on business key). Rerunning the
  script converges to the same state instead of duplicating rows.
* No truncate/drop is performed; existing rows not present in the CSVs are
  left untouched.

Data quality
------------
Rows failing validation are counted per rule and reported at the end; the
script exits non-zero if any file could not be processed. Valid rows are
still loaded, so one bad row never blocks the pipeline.

Usage
-----
    python scripts/ingest_postgres.py [--data-dir ../data]
"""

from __future__ import annotations

import argparse
import logging
import sys
import uuid
from datetime import datetime
from pathlib import Path

import pandas as pd
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session

# Make `app` importable when running as a script.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from app.core.config import settings  # noqa: E402
from app.models import (  # noqa: E402
    Category,
    Inventory,
    Order,
    OrderItem,
    Product,
    Sales,
    Store,
)

logging.basicConfig(level=logging.INFO, format="%(levelname)-7s %(message)s")
log = logging.getLogger("ingest")

UUID_NAMESPACE = uuid.UUID("6f0a1a52-0f0e-4d0e-9a3e-0f1e2d3c4b5a")


def stable_uuid(*parts) -> uuid.UUID:
    """Deterministic UUIDv5 from the source business key."""
    return uuid.uuid5(UUID_NAMESPACE, "|".join(str(p) for p in parts))


class QualityReport:
    """Collects per-file validation failures instead of discarding them silently."""

    def __init__(self) -> None:
        self.issues: dict[str, int] = {}

    def add(self, rule: str, count: int) -> None:
        if count:
            self.issues[rule] = self.issues.get(rule, 0) + count

    def log(self) -> None:
        if self.issues:
            log.warning("Data-quality report (rows affected by rule):")
            for rule, count in sorted(self.issues.items()):
                log.warning("  %-55s %d", rule, count)
        else:
            log.info("Data-quality report: no issues found.")


# --------------------------------------------------------------------------- #
# Per-entity loaders                                                          #
# --------------------------------------------------------------------------- #


def load_categories_and_products(session: Session, path: Path, report: QualityReport) -> None:
    df = pd.read_csv(path)
    report.add("products: missing sku_code", int(df["sku_code"].isna().sum()))
    report.add("products: missing unit/cost price",
               int((df["unit_price"].isna() | df["cost_price"].isna()).sum()))
    report.add("products: duplicate sku_code", int(df["sku_code"].duplicated().sum()))
    df = df.dropna(subset=["sku_code", "unit_price", "cost_price"]).drop_duplicates("sku_code")

    # Categories upserted first (FK-safe), name is the natural key.
    category_names = sorted(df["category"].dropna().unique())
    existing = {c.name: c for c in session.execute(
        select(Category).where(Category.name.in_(category_names))).scalars()}
    for name in category_names:
        if name not in existing:
            cat = Category(name=name)
            session.add(cat)
            existing[name] = cat
    session.flush()
    log.info("categories: %d ensured", len(category_names))

    # Products upsert on sku_code.
    rows, skipped = [], 0
    for rec in df.to_dict("records"):
        cat = existing.get(rec["category"])
        if cat is None:
            skipped += 1
            report.add("products: unknown category", 1)
            continue
        rows.append(
            dict(
                id=stable_uuid("product", rec["product_id"]),
                sku_code=rec["sku_code"],
                product_name=rec["product_name"],
                category_id=cat.id,
                brand=rec["brand"],
                unit_price=float(rec["unit_price"]),
                cost_price=float(rec["cost_price"]),
                must_sell_flag=bool(rec["must_sell_flag"]),
                launch_date=pd.to_datetime(rec["launch_date"]).to_pydatetime()
                if pd.notna(rec["launch_date"]) else None,
            )
        )
    if rows:
        stmt = pg_insert(Product).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Product.sku_code],
            set_={
                "product_name": stmt.excluded.product_name,
                "category_id": stmt.excluded.category_id,
                "brand": stmt.excluded.brand,
                "unit_price": stmt.excluded.unit_price,
                "cost_price": stmt.excluded.cost_price,
                "must_sell_flag": stmt.excluded.must_sell_flag,
                "launch_date": stmt.excluded.launch_date,
            },
        )
        session.execute(stmt)
    log.info("products: %d upserted (%d skipped)", len(rows), skipped)


def load_stores(session: Session, path: Path, report: QualityReport) -> None:
    df = pd.read_csv(path)
    report.add("retailers: missing retailer_id", int(df["retailer_id"].isna().sum()))
    report.add("retailers: out-of-range coordinates",
               int(((df["latitude"].abs() > 90) | (df["longitude"].abs() > 180)).sum()))
    report.add("retailers: duplicate retailer_id", int(df["retailer_id"].duplicated().sum()))
    df = df.dropna(subset=["retailer_id"]).drop_duplicates("retailer_id")
    df = df[(df["latitude"].abs() <= 90) & (df["longitude"].abs() <= 180)]

    rows = [
        dict(
            id=stable_uuid("store", rec["retailer_id"]),
            retailer_id=int(rec["retailer_id"]),
            retailer_name=rec["retailer_name"],
            store_type=rec["store_type"],
            city=rec["city"],
            state=rec["state"],
            region=rec["region"],
            latitude=float(rec["latitude"]),
            longitude=float(rec["longitude"]),
            prosperity_index=float(rec["prosperity_index"]),
            premiumness_index=float(rec["premiumness_index"]),
            store_size_sqft=int(rec["store_size_sqft"]),
            # Geometry column is plain text; keep a readable WKT-style point.
            location=f"POINT({rec['longitude']} {rec['latitude']})",
        )
        for rec in df.to_dict("records")
    ]
    if rows:
        stmt = pg_insert(Store).values(rows)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Store.retailer_id],
            set_={
                "retailer_name": stmt.excluded.retailer_name,
                "store_type": stmt.excluded.store_type,
                "city": stmt.excluded.city,
                "state": stmt.excluded.state,
                "region": stmt.excluded.region,
                "latitude": stmt.excluded.latitude,
                "longitude": stmt.excluded.longitude,
                "prosperity_index": stmt.excluded.prosperity_index,
                "premiumness_index": stmt.excluded.premiumness_index,
                "store_size_sqft": stmt.excluded.store_size_sqft,
                "location": stmt.excluded.location,
            },
        )
        session.execute(stmt)
    log.info("stores: %d upserted", len(rows))


def _read_validated_sales(path: Path, report: QualityReport) -> pd.DataFrame:
    """Shared validation for the sales fact file (used by sales + orders)."""
    df = pd.read_csv(path)

    # Validation with per-rule counts; valid rows are still loaded.
    bad_dates = pd.to_datetime(df["date"], errors="coerce").isna()
    report.add("sales: invalid dates", int(bad_dates.sum()))
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df[~bad_dates]

    for rule, mask in {
        "sales: missing FK ids": df["retailer_id"].isna() | df["product_id"].isna(),
        "sales: non-positive quantity": df["quantity"] <= 0,
        "sales: negative unit_price": df["unit_price"] < 0,
        "sales: negative revenue": df["revenue"] < 0,
        "sales: duplicate sale_id": df["sale_id"].duplicated(),
    }.items():
        report.add(rule, int(mask.sum()))
        df = df[~mask.fillna(True)]
    return df


def load_sales(session: Session, path: Path, report: QualityReport) -> None:
    df = _read_validated_sales(path, report)

    rows = [
        dict(
            id=stable_uuid("sale", rec["sale_id"]),
            retailer_id=int(rec["retailer_id"]),
            product_id=stable_uuid("product", rec["product_id"]),
            date=rec["date"].to_pydatetime(),
            channel=rec["channel"],
            quantity=int(rec["quantity"]),
            unit_price=float(rec["unit_price"]),
            # Source revenue is gross (pre-discount): qty*price; verified
            # against monthly_kpis.csv totals during ingestion design.
            revenue=float(rec["revenue"]),
            discount_percent=float(rec["discount_pct"]),
        )
        for rec in df.to_dict("records")
    ]

    # Batch upserts on the deterministic PK.
    total = 0
    for start in range(0, len(rows), 5000):
        chunk = rows[start:start + 5000]
        stmt = pg_insert(Sales).values(chunk)
        stmt = stmt.on_conflict_do_update(
            index_elements=[Sales.id],
            set_={
                "quantity": stmt.excluded.quantity,
                "unit_price": stmt.excluded.unit_price,
                "revenue": stmt.excluded.revenue,
                "discount_percent": stmt.excluded.discount_percent,
            },
        )
        session.execute(stmt)
        total += len(chunk)
        log.info("sales: %d/%d upserted", total, len(rows))


def load_orders(session: Session, path: Path, report: QualityReport) -> None:
    """Load each validated sales transaction as a single-line order.

    Deterministic mapping (documented in the module docstring):
      order.id         = stable_uuid("order", sale_id)
      order_number     = SALE-<sale_id>
      order_items.id   = stable_uuid("order_item", sale_id)
      total_price      = qty * unit_price          (GROSS, matches source revenue)
      discount_amount  = gross - net               (order header)
      total_revenue    = net                       (order header)
    """
    df = _read_validated_sales(path, report)

    order_rows, item_rows = [], []
    for rec in df.to_dict("records"):
        # The source `revenue` column is authoritative GROSS (pre-discount)
        # qty*unit_price rounded to 2dp (verified against monthly_kpis.csv).
        gross = round(float(rec["revenue"]), 2)
        net = round(gross * (1 - float(rec["discount_pct"]) / 100.0), 2)
        order_rows.append(
            dict(
                id=stable_uuid("order", rec["sale_id"]),
                order_number=f"SALE-{rec['sale_id']}",
                store_id=stable_uuid("store", rec["retailer_id"]),
                customer_id=None,  # no customer dimension in the source
                total_amount=gross,
                total_items=int(rec["quantity"]),
                total_revenue=net,
                discount_amount=round(gross - net, 2),
                status="completed",
                payment_method=None,
                created_at=rec["date"].to_pydatetime(),
            )
        )
        item_rows.append(
            dict(
                id=stable_uuid("order_item", rec["sale_id"]),
                order_id=stable_uuid("order", rec["sale_id"]),
                product_id=stable_uuid("product", rec["product_id"]),
                retailer_id=int(rec["retailer_id"]),
                product_sku="",  # filled below from the product map
                product_name="",
                category_name=None,
                quantity=int(rec["quantity"]),
                unit_price=float(rec["unit_price"]),
                total_price=gross,
                discount_percent=float(rec["discount_pct"]),
            )
        )

    # Denormalized line fields: resolve sku/name/category per product.
    product_map = {
        p.id: (p.sku_code, p.product_name, p.category_id)
        for p in session.execute(select(Product)).scalars()
    }
    category_map = {
        c.id: c.name for c in session.execute(select(Category)).scalars()
    }
    for row in item_rows:
        sku, name, cat_id = product_map[row["product_id"]]
        row["product_sku"] = sku
        row["product_name"] = name
        row["category_name"] = category_map.get(cat_id)

    for rows, model, conflict_key, update_cols in (
        (order_rows, Order, Order.order_number,
         ["store_id", "total_amount", "total_items", "total_revenue",
          "discount_amount", "status", "created_at"]),
        (item_rows, OrderItem, OrderItem.id,
         ["product_id", "product_sku", "product_name", "category_name",
          "quantity", "unit_price", "total_price", "discount_percent"]),
    ):
        total = 0
        for start in range(0, len(rows), 5000):
            chunk = rows[start:start + 5000]
            stmt = pg_insert(model).values(chunk)
            stmt = stmt.on_conflict_do_update(
                index_elements=[conflict_key],
                set_={c: stmt.excluded[c] for c in update_cols},
            )
            session.execute(stmt)
            total += len(chunk)
        log.info("%s: %d upserted", model.__tablename__, total)


def load_inventory(session: Session, path: Path, report: QualityReport) -> None:
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"], errors="coerce")
    report.add("inventory: invalid dates", int(df["date"].isna().sum()))
    df = df[df["date"].notna()]

    for rule, mask in {
        "inventory: missing FK ids": df["retailer_id"].isna() | df["product_id"].isna(),
        "inventory: negative stock_level": df["stock_level"] < 0,
        "inventory: non-positive reorder_point": df["reorder_point"] <= 0,
    }.items():
        report.add(rule, int(mask.sum()))
        df = df[~mask.fillna(True)]

    # The model stores current state only (UNIQUE product_id+retailer_id),
    # so keep the LATEST snapshot per pair. Historical time series would need
    # a schema change; reported as a known limitation.
    total_snapshots = len(df)
    df = df.sort_values("date").drop_duplicates(
        ["retailer_id", "product_id"], keep="last"
    )
    report.add(
        "inventory: older snapshots collapsed to latest per (retailer,product)",
        total_snapshots - len(df),
    )

    rows = [
        dict(
            id=stable_uuid("inventory", rec["retailer_id"], rec["product_id"]),
            product_id=stable_uuid("product", rec["product_id"]),
            retailer_id=int(rec["retailer_id"]),
            quantity_on_hand=int(rec["stock_level"]),
            quantity_reserved=0,
            quantity_available=int(rec["stock_level"]),
            reorder_point=int(rec["reorder_point"]),
            reorder_quantity=max(int(rec["reorder_point"]), 20),
            last_restocked=rec["date"].to_pydatetime(),
        )
        for rec in df.to_dict("records")
    ]

    total = 0
    for start in range(0, len(rows), 5000):
        chunk = rows[start:start + 5000]
        stmt = pg_insert(Inventory).values(chunk)
        stmt = stmt.on_conflict_do_update(
            constraint="uq_inventory_product_retailer",
            set_={
                "quantity_on_hand": stmt.excluded.quantity_on_hand,
                "quantity_available": stmt.excluded.quantity_available,
                "reorder_point": stmt.excluded.reorder_point,
                "reorder_quantity": stmt.excluded.reorder_quantity,
                "last_restocked": stmt.excluded.last_restocked,
            },
        )
        session.execute(stmt)
        total += len(chunk)
        log.info("inventory: %d/%d upserted", total, len(rows))


# --------------------------------------------------------------------------- #
# Verification                                                                #
# --------------------------------------------------------------------------- #


def verify(session: Session) -> bool:
    from sqlalchemy import func

    counts = {}
    for name, model in {
        "categories": Category,
        "products": Product,
        "stores": Store,
        "orders": Order,
        "order_items": OrderItem,
        "sales": Sales,
        "inventory": Inventory,
    }.items():
        counts[name] = session.execute(select(func.count()).select_from(model)).scalar()

    log.info("Row counts after ingestion:")
    for name, count in counts.items():
        log.info("  %-24s %d", name, count)

    ok = counts["products"] > 0 and counts["stores"] > 0 and counts["sales"] > 0

    # Referential integrity: sales rows must point at real products/stores.
    orphan_sales = session.execute(
        select(Sales.id)
        .outerjoin(Product, Sales.product_id == Product.id)
        .where(Product.id.is_(None))
        .limit(1)
    ).first()
    orphan_inv = session.execute(
        select(Inventory.id)
        .outerjoin(Product, Inventory.product_id == Product.id)
        .where(Product.id.is_(None))
        .limit(1)
    ).first()
    if orphan_sales:
        log.error("Referential integrity: sales rows without a matching product!")
        ok = False
    if orphan_inv:
        log.error("Referential integrity: inventory rows without a matching product!")
        ok = False

    # Independent aggregate cross-check: sum of sales.revenue.
    total = session.execute(select(func.coalesce(func.sum(Sales.revenue), 0.0))).scalar()
    log.info("Independent sum(sales.revenue) = %.2f", total)
    return ok


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", default=str(Path(__file__).resolve().parent.parent.parent / "data"))
    args = parser.parse_args()
    data_dir = Path(args.data_dir)

    log.info("Target database: %s", settings.database_url.split("@")[-1])
    report = QualityReport()

    from app.database import SessionLocal, init_db

    init_db()  # safe: create_all is idempotent
    session = SessionLocal()
    started = datetime.now()

    # One transaction per entity: long single transactions over a pooled
    # cloud connection are prone to mid-flight disconnects. Every loader is
    # an upsert keyed on business identity, so a rerun after a partial
    # failure converges to the same state without duplicating rows.
    steps = [
        ("products", load_categories_and_products, "products.csv"),
        ("stores", load_stores, "retailers.csv"),
        ("sales", load_sales, "sales_transactions.csv"),
        ("orders", load_orders, "sales_transactions.csv"),
        ("inventory", load_inventory, "inventory.csv"),
    ]
    try:
        for name, loader, filename in steps:
            step_started = datetime.now()
            loader(session, data_dir / filename, report)
            session.commit()
            log.info(
                "%s: committed in %.1fs",
                name,
                (datetime.now() - step_started).total_seconds(),
            )
        log.info("Ingestion completed in %.1fs", (datetime.now() - started).total_seconds())
        report.log()
        return 0 if verify(session) else 1
    except Exception:
        session.rollback()
        log.exception("Ingestion failed; current entity transaction rolled back. Rerun to resume.")
        return 1
    finally:
        session.close()


if __name__ == "__main__":
    sys.exit(main())
