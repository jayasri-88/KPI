from pathlib import Path

import pandas as pd
from pymongo import ASCENDING, DESCENDING

from app.core.config import settings
from app.db.mongodb import database


PROJECT_ROOT = Path(__file__).resolve().parents[2]
DATA_DIR = PROJECT_ROOT / "data"


def dataframe_to_records(df: pd.DataFrame):
    records = df.to_dict("records")

    for record in records:
        for key, value in record.items():
            if pd.isna(value):
                record[key] = None
            elif isinstance(value, pd.Timestamp):
                record[key] = value.to_pydatetime()

    return records


def load_products():
    print("\nLoading products.csv...")

    df = pd.read_csv(DATA_DIR / "products.csv")

    df["launch_date"] = pd.to_datetime(df["launch_date"])

    records = dataframe_to_records(df)

    collection = database["products"]

    collection.delete_many({})

    if records:
        collection.insert_many(records)

    print(f"products: {len(records)} records inserted")


def load_retailers():
    print("\nLoading retailers.csv...")

    df = pd.read_csv(DATA_DIR / "retailers.csv")

    records = []

    for row in df.to_dict("records"):
        records.append(
            {
                "retailer_id": int(row["retailer_id"]),
                "retailer_name": row["retailer_name"],
                "store_type": row["store_type"],
                "city": row["city"],
                "state": row["state"],
                "region": row["region"],
                "latitude": float(row["latitude"]),
                "longitude": float(row["longitude"]),
                "prosperity_index": float(
                    row["prosperity_index"]
                ),
                "premiumness_index": float(
                    row["premiumness_index"]
                ),
                "store_size_sqft": int(
                    row["store_size_sqft"]
                ),
                "location": {
                    "type": "Point",
                    "coordinates": [
                        float(row["longitude"]),
                        float(row["latitude"]),
                    ],
                },
            }
        )

    collection = database["retailers"]

    collection.delete_many({})

    if records:
        collection.insert_many(records)

    print(
        f"retailers: {len(records)} records inserted"
    )


def load_sales():
    print("\nLoading sales_transactions.csv...")

    df = pd.read_csv(
        DATA_DIR / "sales_transactions.csv"
    )

    df["date"] = pd.to_datetime(df["date"])

    records = dataframe_to_records(df)

    collection = database["sales_transactions"]

    collection.delete_many({})

    batch_size = 1000

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        collection.insert_many(batch)

        print(
            f"Inserted sales records "
            f"{min(start + batch_size, len(records))}"
            f"/{len(records)}",
            end="\r",
        )

    print(
        f"\nsales_transactions: "
        f"{len(records)} records inserted"
    )


def load_inventory():
    print("\nLoading inventory.csv...")

    df = pd.read_csv(
        DATA_DIR / "inventory.csv"
    )

    df["date"] = pd.to_datetime(df["date"])

    records = dataframe_to_records(df)

    collection = database["inventory"]

    collection.delete_many({})

    batch_size = 1000

    for start in range(0, len(records), batch_size):
        batch = records[start:start + batch_size]

        collection.insert_many(batch)

        print(
            f"Inserted inventory records "
            f"{min(start + batch_size, len(records))}"
            f"/{len(records)}",
            end="\r",
        )

    print(
        f"\ninventory: "
        f"{len(records)} records inserted"
    )


def load_monthly_kpis():
    print("\nLoading monthly_kpis.csv...")

    df = pd.read_csv(
        DATA_DIR / "monthly_kpis.csv"
    )

    records = dataframe_to_records(df)

    collection = database["monthly_kpis"]

    collection.delete_many({})

    if records:
        collection.insert_many(records)

    print(
        f"monthly_kpis: "
        f"{len(records)} records inserted"
    )


def create_indexes():
    print("\nCreating indexes...")

    database.products.create_index(
        [("product_id", ASCENDING)],
        unique=True,
    )

    database.products.create_index(
        [("sku_code", ASCENDING)],
        unique=True,
    )

    database.products.create_index(
        [("category", ASCENDING)]
    )

    database.retailers.create_index(
        [("retailer_id", ASCENDING)],
        unique=True,
    )

    database.retailers.create_index(
        [("region", ASCENDING)]
    )

    database.retailers.create_index(
        [("city", ASCENDING)]
    )

    database.retailers.create_index(
        [("location", "2dsphere")]
    )

    database.sales_transactions.create_index(
        [("date", DESCENDING)]
    )

    database.sales_transactions.create_index(
        [
            ("product_id", ASCENDING),
            ("date", DESCENDING),
        ]
    )

    database.sales_transactions.create_index(
        [
            ("retailer_id", ASCENDING),
            ("date", DESCENDING),
        ]
    )

    database.sales_transactions.create_index(
        [("channel", ASCENDING)]
    )

    database.inventory.create_index(
        [("date", DESCENDING)]
    )

    database.inventory.create_index(
        [
            ("product_id", ASCENDING),
            ("retailer_id", ASCENDING),
            ("date", DESCENDING),
        ]
    )

    database.monthly_kpis.create_index(
        [
            ("month", DESCENDING),
            ("region", ASCENDING),
            ("category", ASCENDING),
        ]
    )

    print("Indexes created successfully.")


def verify_data():
    print("\nVerifying database...")

    expected_counts = {
        "products": 80,
        "retailers": 120,
        "sales_transactions": 90820,
        "inventory": 59217,
        "monthly_kpis": 360,
    }

    all_valid = True

    for collection_name, expected in expected_counts.items():
        actual = database[collection_name].count_documents({})

        status = "OK" if actual == expected else "ERROR"

        print(
            f"{collection_name}: "
            f"{actual}/{expected} [{status}]"
        )

        if actual != expected:
            all_valid = False

    retailer = database.retailers.find_one(
        {"retailer_id": 1}
    )

    if retailer and "location" in retailer:
        print("Geospatial location: OK")
    else:
        print("Geospatial location: ERROR")
        all_valid = False

    if all_valid:
        print("\nDATA VERIFICATION PASSED")
    else:
        print("\nDATA VERIFICATION FAILED")


def main():
    print("=" * 50)
    print("Retail Intelligence Agent")
    print("MongoDB Data Ingestion")
    print("=" * 50)

    print(f"Database: {settings.mongodb_database}")
    print(f"Data directory: {DATA_DIR}")

    load_products()
    load_retailers()
    load_sales()
    load_inventory()
    load_monthly_kpis()

    create_indexes()

    verify_data()

    print("\nIngestion complete.")


if __name__ == "__main__":
    main()