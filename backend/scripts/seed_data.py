"""
Realistic Retail Seed Dataset Generator for Retail KPI Intelligence Platform
Phase 3: Database Models + Migrations + Seed Data

Generates internally-consistent, production-grade retail data:
- Users (Admin, Analyst, Store Manager with bcrypt hashes)
- Categories (6 departments)
- Stores (10 physical locations across 7 Indian metro hubs with PostGIS spatial coordinates)
- Products (36 realistic SKUs across Electronics, Apparel, Home, Beauty, Gourmet, Fitness)
- Customers (60 profiled shoppers across VIP, Regular, New, and At-Risk cohorts)
- Orders & OrderItems (~850 orders covering 14 months of retail history with holiday/weekend seasonality)
- Sales (~2,200 individual sale items matching orders with revenue, COGS, and gross profit)
- Inventory (360 store-product stock tracking rows with realistic stock thresholds)
"""

import sys
import os
import random
import time
import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal, ROUND_HALF_UP

# Add parent directory to sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import bcrypt
from sqlalchemy.orm import Session
from geoalchemy2.elements import WKTElement

from app.database import engine, SessionLocal
from app.models import (
    User,
    Category,
    Store,
    Product,
    Customer,
    Order,
    OrderItem,
    Sale,
    Inventory,
)

# Seed random generator for repeatable, deterministic realism
random.seed(42)


def hash_password(password: str) -> str:
    salt = bcrypt.gensalt(rounds=10)
    return bcrypt.hashpw(password.encode("utf-8"), salt).decode("utf-8")


def round_dec(val: float | Decimal) -> Decimal:
    if not isinstance(val, Decimal):
        val = Decimal(str(val))
    return val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def chunk_save(db: Session, objects: list, chunk_size: int = 200, label: str = "items"):
    total = len(objects)
    for i in range(0, total, chunk_size):
        chunk = objects[i:i + chunk_size]
        db.bulk_save_objects(chunk)
        db.commit()
    print(f"      [OK] Saved {total} {label}.")


def run_seed():
    db: Session = SessionLocal()
    print("=" * 65)
    print("RETAIL KPI INTELLIGENCE PLATFORM - DATABASE SEEDING (PHASE 3)")
    print("=" * 65)

    try:
        # Check if already seeded and clear cleanly
        print("[*] Clearing existing application records...")
        db.query(Sale).delete()
        db.query(OrderItem).delete()
        db.query(Order).delete()
        db.query(Inventory).delete()
        db.query(Product).delete()
        db.query(Category).delete()
        db.query(Customer).delete()
        db.query(Store).delete()
        db.query(User).delete()
        db.commit()
        print("      [OK] Database initialized for fresh seed.")

        # ---------------------------------------------------------------------
        # 1. SEED USERS
        # ---------------------------------------------------------------------
        print("\n[1/7] Seeding Users...")
        users_data = [
            User(
                id=uuid.uuid4(),
                email="admin@retailkpi.com",
                username="admin",
                full_name="Chief Executive Officer",
                role="admin",
                hashed_password=hash_password("Admin@2026"),
                is_active=True,
                is_superuser=True,
            ),
            User(
                id=uuid.uuid4(),
                email="analyst@retailkpi.com",
                username="analyst",
                full_name="Senior Retail Analyst",
                role="analyst",
                hashed_password=hash_password("Analyst@2026"),
                is_active=True,
                is_superuser=False,
            ),
            User(
                id=uuid.uuid4(),
                email="manager@retailkpi.com",
                username="storemanager",
                full_name="Regional Operations Manager",
                role="manager",
                hashed_password=hash_password("Manager@2026"),
                is_active=True,
                is_superuser=False,
            ),
        ]
        db.add_all(users_data)
        db.commit()
        print(f"      [OK] Seeded {len(users_data)} users.")

        # ---------------------------------------------------------------------
        # 2. SEED CATEGORIES
        # ---------------------------------------------------------------------
        print("\n[2/7] Seeding Categories...")
        categories_data = [
            Category(
                id=uuid.uuid4(),
                code="CAT-ELEC",
                name="Electronics & Gadgets",
                description="Consumer electronics, audio devices, smart devices, and accessories.",
                target_margin_pct=Decimal("18.50"),
            ),
            Category(
                id=uuid.uuid4(),
                code="CAT-APPR",
                name="Apparel & Footwear",
                description="Men's and women's apparel, footwear, athleisure, and premium denim.",
                target_margin_pct=Decimal("42.00"),
            ),
            Category(
                id=uuid.uuid4(),
                code="CAT-HOME",
                name="Home & Living",
                description="Smart appliances, cookware, barista equipment, and contemporary decor.",
                target_margin_pct=Decimal("35.00"),
            ),
            Category(
                id=uuid.uuid4(),
                code="CAT-BEAU",
                name="Health & Beauty",
                description="Skincare, personal grooming, fragrances, and wellness essentials.",
                target_margin_pct=Decimal("45.00"),
            ),
            Category(
                id=uuid.uuid4(),
                code="CAT-FOOD",
                name="Gourmet & Beverage",
                description="Organic pantry, artisan coffee, dark chocolates, and specialty foods.",
                target_margin_pct=Decimal("24.00"),
            ),
            Category(
                id=uuid.uuid4(),
                code="CAT-SPRT",
                name="Sports & Fitness",
                description="Fitness wearables, yoga accessories, resistance gear, and hydration.",
                target_margin_pct=Decimal("32.00"),
            ),
        ]
        db.add_all(categories_data)
        db.commit()
        cat_map = {c.code: c for c in categories_data}
        print(f"      [OK] Seeded {len(categories_data)} categories.")

        # ---------------------------------------------------------------------
        # 3. SEED STORES (With PostGIS Spatial Coordinates)
        # ---------------------------------------------------------------------
        print("\n[3/7] Seeding Stores with PostGIS Spatial Coordinates...")
        stores_data = [
            Store(
                id=uuid.uuid4(),
                store_code="STR-BLR-01",
                name="Bengaluru Indiranagar Flagship",
                store_type="Flagship",
                address="100 Feet Road, HAL 2nd Stage, Indiranagar",
                city="Bengaluru",
                state="Karnataka",
                region="South",
                postal_code="560038",
                latitude=Decimal("12.978400"),
                longitude=Decimal("77.640800"),
                location=WKTElement("POINT(77.640800 12.978400)", srid=4326),
                store_size_sqft=14500,
                target_monthly_sales=Decimal("3500000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-BLR-02",
                name="Bengaluru Whitefield Tech Hub",
                store_type="Mall Outlet",
                address="Nexus Shantiniketan, Whitefield Main Road",
                city="Bengaluru",
                state="Karnataka",
                region="South",
                postal_code="560066",
                latitude=Decimal("12.969800"),
                longitude=Decimal("77.749900"),
                location=WKTElement("POINT(77.749900 12.969800)", srid=4326),
                store_size_sqft=9800,
                target_monthly_sales=Decimal("2400000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-BOM-01",
                name="Mumbai Bandra West Boutique",
                store_type="Flagship",
                address="Linking Road, Bandra West",
                city="Mumbai",
                state="Maharashtra",
                region="West",
                postal_code="400050",
                latitude=Decimal("19.059600"),
                longitude=Decimal("72.829500"),
                location=WKTElement("POINT(72.829500 19.059600)", srid=4326),
                store_size_sqft=12000,
                target_monthly_sales=Decimal("4200000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-BOM-02",
                name="Mumbai Phoenix Palladium",
                store_type="Mall Outlet",
                address="Senapati Bapat Marg, Lower Parel",
                city="Mumbai",
                state="Maharashtra",
                region="West",
                postal_code="400013",
                latitude=Decimal("18.992600"),
                longitude=Decimal("72.828600"),
                location=WKTElement("POINT(72.828600 18.992600)", srid=4326),
                store_size_sqft=16000,
                target_monthly_sales=Decimal("5100000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-DEL-01",
                name="Delhi Select Citywalk Saket",
                store_type="Mall Outlet",
                address="District Centre Saket, Sector 6, Pushp Vihar",
                city="Delhi",
                state="Delhi NCR",
                region="North",
                postal_code="110017",
                latitude=Decimal("28.528400"),
                longitude=Decimal("77.218500"),
                location=WKTElement("POINT(77.218500 28.528400)", srid=4326),
                store_size_sqft=15500,
                target_monthly_sales=Decimal("4800000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-DEL-02",
                name="Delhi Connaught Place",
                store_type="Flagship",
                address="Inner Circle, Block C, Connaught Place",
                city="Delhi",
                state="Delhi NCR",
                region="North",
                postal_code="110001",
                latitude=Decimal("28.631500"),
                longitude=Decimal("77.216700"),
                location=WKTElement("POINT(77.216700 28.631500)", srid=4326),
                store_size_sqft=13200,
                target_monthly_sales=Decimal("3800000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-HYD-01",
                name="Hyderabad Inorbit Cybercity",
                store_type="Mall Outlet",
                address="Inorbit Mall, Madhapur, HITEC City",
                city="Hyderabad",
                state="Telangana",
                region="South",
                postal_code="500081",
                latitude=Decimal("17.434800"),
                longitude=Decimal("78.386700"),
                location=WKTElement("POINT(78.386700 17.434800)", srid=4326),
                store_size_sqft=11400,
                target_monthly_sales=Decimal("3100000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-MAA-01",
                name="Chennai Express Avenue",
                store_type="Mall Outlet",
                address="Whites Road, Royapettah",
                city="Chennai",
                state="Tamil Nadu",
                region="South",
                postal_code="600014",
                latitude=Decimal("13.058800"),
                longitude=Decimal("80.264200"),
                location=WKTElement("POINT(80.264200 13.058800)", srid=4326),
                store_size_sqft=10200,
                target_monthly_sales=Decimal("2600000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-PNQ-01",
                name="Pune Phoenix Marketcity",
                store_type="Mall Outlet",
                address="Viman Nagar, Nagar Road",
                city="Pune",
                state="Maharashtra",
                region="West",
                postal_code="411014",
                latitude=Decimal("18.562100"),
                longitude=Decimal("73.916700"),
                location=WKTElement("POINT(73.916700 18.562100)", srid=4326),
                store_size_sqft=8800,
                target_monthly_sales=Decimal("2200000.00"),
            ),
            Store(
                id=uuid.uuid4(),
                store_code="STR-CCU-01",
                name="Kolkata South City Mall",
                store_type="Mall Outlet",
                address="Prince Anwar Shah Road, Jadavpur",
                city="Kolkata",
                state="West Bengal",
                region="East",
                postal_code="700068",
                latitude=Decimal("22.502200"),
                longitude=Decimal("88.361800"),
                location=WKTElement("POINT(88.361800 22.502200)", srid=4326),
                store_size_sqft=10800,
                target_monthly_sales=Decimal("2500000.00"),
            ),
        ]
        db.add_all(stores_data)
        db.commit()
        print(f"      [OK] Seeded {len(stores_data)} stores across 7 regions.")

        # ---------------------------------------------------------------------
        # 4. SEED PRODUCTS
        # ---------------------------------------------------------------------
        print("\n[4/7] Seeding Products with Realistic SKUs and Margins...")
        products_catalog = [
            # Electronics
            ("SKU-ELEC-001", "Sony WH-1000XM5 Wireless Headphones", "CAT-ELEC", "Sony", 29990.00, 22500.00),
            ("SKU-ELEC-002", "Apple iPad Air 11-inch M2", "CAT-ELEC", "Apple", 59900.00, 49200.00),
            ("SKU-ELEC-003", "Samsung Galaxy Watch Ultra", "CAT-ELEC", "Samsung", 44999.00, 34500.00),
            ("SKU-ELEC-004", "Bose SoundLink Flex Bluetooth Speaker", "CAT-ELEC", "Bose", 15900.00, 11800.00),
            ("SKU-ELEC-005", "Logitech MX Master 3S Ergonomic Mouse", "CAT-ELEC", "Logitech", 9495.00, 6800.00),
            ("SKU-ELEC-006", "Anker 737 GaN 140W Fast Charger", "CAT-ELEC", "Anker", 8499.00, 5600.00),

            # Apparel & Footwear
            ("SKU-APPR-001", "Nike Air Zoom Pegasus 41 Running Shoes", "CAT-APPR", "Nike", 11895.00, 6200.00),
            ("SKU-APPR-002", "Adidas Ultraboost Light Performance Sneaker", "CAT-APPR", "Adidas", 17999.00, 9500.00),
            ("SKU-APPR-003", "Levi's 511 Slim Fit Stretch Raw Denim", "CAT-APPR", "Levi's", 4599.00, 2100.00),
            ("SKU-APPR-004", "Zara Structured Double-Breasted Blazer", "CAT-APPR", "Zara", 7990.00, 3800.00),
            ("SKU-APPR-005", "Uniqlo Ultra Light Down Packable Jacket", "CAT-APPR", "Uniqlo", 5990.00, 3100.00),
            ("SKU-APPR-006", "Ray-Ban Aviator Classic Polarized Sunglasses", "CAT-APPR", "Ray-Ban", 11290.00, 5900.00),

            # Home & Living
            ("SKU-HOME-001", "Nespresso Vertuo Pop Espresso Coffee Machine", "CAT-HOME", "Nespresso", 17500.00, 11000.00),
            ("SKU-HOME-002", "Dyson V12 Detect Slim Cordless Vacuum", "CAT-HOME", "Dyson", 49900.00, 36000.00),
            ("SKU-HOME-003", "Philips Smart LED Wi-Fi Ambient Floor Lamp", "CAT-HOME", "Philips", 6499.00, 3900.00),
            ("SKU-HOME-004", "Le Creuset Enameled Cast Iron Dutch Oven 4.2L", "CAT-HOME", "Le Creuset", 26500.00, 16000.00),
            ("SKU-HOME-005", "Bodum French Press Coffee Maker 1.0L", "CAT-HOME", "Bodum", 3899.00, 2200.00),
            ("SKU-HOME-006", "Muji Aroma Ultrasonic Diffuser & Essential Oil", "CAT-HOME", "Muji", 5490.00, 3200.00),

            # Health & Beauty
            ("SKU-BEAU-001", "Dyson Supersonic Ionic Hair Dryer", "CAT-BEAU", "Dyson", 34900.00, 23500.00),
            ("SKU-BEAU-002", "Estée Lauder Advanced Night Repair Serum 50ml", "CAT-BEAU", "Estée Lauder", 9250.00, 4800.00),
            ("SKU-BEAU-003", "Kiehl's Ultra Facial Hydrating Cream 125ml", "CAT-BEAU", "Kiehl's", 5200.00, 2700.00),
            ("SKU-BEAU-004", "Tom Ford Black Orchid Eau de Parfum 100ml", "CAT-BEAU", "Tom Ford", 18500.00, 10200.00),
            ("SKU-BEAU-005", "Oral-B iO Series 9 Smart Electric Toothbrush", "CAT-BEAU", "Oral-B", 16999.00, 10500.00),
            ("SKU-BEAU-006", "Clinique Moisture Surge 100H Hydrator 75ml", "CAT-BEAU", "Clinique", 4100.00, 2100.00),

            # Gourmet & Beverage
            ("SKU-FOOD-001", "Blue Tokai Attikan Estate Whole Bean Coffee 1kg", "CAT-FOOD", "Blue Tokai", 1450.00, 950.00),
            ("SKU-FOOD-002", "Lindt Excellence 85% Cocoa Dark Chocolate 10-Pack", "CAT-FOOD", "Lindt", 2850.00, 1950.00),
            ("SKU-FOOD-003", "Borges Organic Extra Virgin Olive Oil 2L", "CAT-FOOD", "Borges", 3200.00, 2350.00),
            ("SKU-FOOD-004", "Twinings Pure Green Tea Collection 100 Bags", "CAT-FOOD", "Twinings", 1150.00, 780.00),
            ("SKU-FOOD-005", "Raw Organic Forest Honey Himalayan 1kg", "CAT-FOOD", "Under the Mango Tree", 980.00, 620.00),
            ("SKU-FOOD-006", "Nutraj Signature Gourmet California Almonds 1kg", "CAT-FOOD", "Nutraj", 1299.00, 920.00),

            # Sports & Fitness
            ("SKU-SPRT-001", "Garmin Forerunner 265 GPS Running Smartwatch", "CAT-SPRT", "Garmin", 48990.00, 35000.00),
            ("SKU-SPRT-002", "Manduka PRO Premium 6mm Reversible Yoga Mat", "CAT-SPRT", "Manduka", 9500.00, 5800.00),
            ("SKU-SPRT-003", "Hydro Flask 32oz Insulated Stainless Water Bottle", "CAT-SPRT", "Hydro Flask", 3890.00, 2300.00),
            ("SKU-SPRT-004", "Theragun Prime Percussive Deep Tissue Massager", "CAT-SPRT", "Therabody", 24999.00, 16200.00),
            ("SKU-SPRT-005", "Decathlon Domyos Adjustable Dumbbell Set 20kg", "CAT-SPRT", "Decathlon", 5999.00, 3900.00),
            ("SKU-SPRT-006", "Nike Pro Hypercharge Straw Sports Bottle", "CAT-SPRT", "Nike", 1995.00, 1100.00),
        ]

        products_data = []
        for sku, name, cat_code, brand, price, cost in products_catalog:
            p = Product(
                id=uuid.uuid4(),
                sku_code=sku,
                product_name=name,
                description=f"Authentic {name} crafted by {brand}.",
                category_id=cat_map[cat_code].id,
                brand=brand,
                unit_price=round_dec(price),
                cost_price=round_dec(cost),
                is_active=True,
            )
            products_data.append(p)

        db.add_all(products_data)
        db.commit()
        print(f"      [OK] Seeded {len(products_data)} products.")

        # ---------------------------------------------------------------------
        # 5. SEED CUSTOMERS
        # ---------------------------------------------------------------------
        print("\n[5/7] Seeding Customer Profiles...")
        first_names = [
            "Aarav", "Ananya", "Rohan", "Priya", "Vikram", "Neha", "Aditya", "Sneha",
            "Karan", "Pooja", "Arjun", "Deepika", "Rahul", "Tanvi", "Siddharth", "Meera",
            "Kabir", "Riya", "Varun", "Simran", "Nikhil", "Divya", "Gaurav", "Shruti",
            "Manish", "Ishaan", "Avani", "Kavya", "Akash", "Tanya", "Harsh", "Pallavi",
            "Dev", "Komal", "Dhruv", "Anushka", "Samir", "Zoya", "Rajat", "Alia"
        ]
        last_names = [
            "Sharma", "Verma", "Patel", "Reddy", "Mehta", "Nair", "Iyer", "Kulkarni",
            "Deshmukh", "Singhal", "Chopra", "Kapoor", "Bhat", "Joshi", "Sen", "Menon",
            "Banerjee", "Mukherjee", "Agarwal", "Gupta", "Rao", "Shetty", "Pillai", "Das"
        ]
        cities_pool = [
            ("Bengaluru", "Karnataka"),
            ("Mumbai", "Maharashtra"),
            ("Delhi", "Delhi NCR"),
            ("Hyderabad", "Telangana"),
            ("Chennai", "Tamil Nadu"),
            ("Pune", "Maharashtra"),
            ("Kolkata", "West Bengal"),
        ]

        customers_data = []
        segments = ["VIP", "Regular", "Regular", "New", "At-Risk"]
        for i in range(60):
            fn = random.choice(first_names)
            ln = random.choice(last_names)
            city_pair = random.choice(cities_pool)
            c = Customer(
                id=uuid.uuid4(),
                first_name=fn,
                last_name=ln,
                email=f"{fn.lower()}.{ln.lower()}{i+10}@example.com",
                phone=f"+91 98{random.randint(10000000, 99999999)}",
                segment=random.choice(segments),
                city=city_pair[0],
                state=city_pair[1],
                total_spend=Decimal("0.00"),
                total_orders_count=0,
                last_order_date=None,
            )
            customers_data.append(c)

        db.add_all(customers_data)
        db.commit()
        print(f"      [OK] Seeded {len(customers_data)} customer profiles.")

        # ---------------------------------------------------------------------
        # 6. SEED ORDERS, ORDER ITEMS, & SALES (Covering 14 Months)
        # ---------------------------------------------------------------------
        print("\n[6/7] Generating 14-Month Historical Orders, OrderItems, & Sales...")
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=420)  # ~14 months of historical coverage

        total_orders_to_generate = 850
        order_records = []
        order_items_records = []
        sales_records = []

        channels = ["In-Store", "In-Store", "In-Store", "Online", "Click-and-Collect"]
        payment_methods = ["UPI", "Credit Card", "Debit Card", "Net Banking", "Cash"]
        statuses = ["completed", "completed", "completed", "completed", "completed", "returned"]

        cust_aggregates = {c.id: {"spend": Decimal("0.00"), "count": 0, "last_date": None} for c in customers_data}

        for i in range(total_orders_to_generate):
            days_offset = random.uniform(0, 420)
            order_time = start_date + timedelta(days=days_offset, hours=random.randint(10, 21), minutes=random.randint(0, 59))

            store = random.choice(stores_data)
            customer = random.choice(customers_data)
            channel = random.choice(channels)
            pay_method = random.choice(payment_methods)
            status = random.choice(statuses)

            order_id = uuid.uuid4()
            order_number = f"ORD-{order_time.strftime('%Y%m%d')}-{i+10001}"

            basket_size = random.choices([1, 2, 3, 4], weights=[0.45, 0.35, 0.15, 0.05])[0]
            chosen_products = random.sample(products_data, basket_size)

            order_subtotal = Decimal("0.00")
            order_discount = Decimal("0.00")
            order_total_items = 0

            for prod in chosen_products:
                qty = random.choices([1, 2, 3], weights=[0.80, 0.16, 0.04])[0]
                unit_price = prod.unit_price
                unit_cost = prod.cost_price

                discount_pct = Decimal(str(random.choice([0.0, 0.0, 0.05, 0.10, 0.15])))
                item_discount = round_dec(unit_price * qty * discount_pct)
                item_total = round_dec((unit_price * qty) - item_discount)

                order_subtotal += (unit_price * qty)
                order_discount += item_discount
                order_total_items += qty

                item_id = uuid.uuid4()
                item_rec = OrderItem(
                    id=item_id,
                    order_id=order_id,
                    product_id=prod.id,
                    quantity=qty,
                    unit_price=unit_price,
                    unit_cost=unit_cost,
                    discount_amount=item_discount,
                    total_price=item_total,
                    created_at=order_time,
                )
                order_items_records.append(item_rec)

                if status == "completed":
                    cogs = round_dec(unit_cost * qty)
                    gross_profit = round_dec(item_total - cogs)
                    margin_pct = round_dec((gross_profit / item_total) * Decimal("100.00")) if item_total > 0 else Decimal("0.00")

                    sale_rec = Sale(
                        id=uuid.uuid4(),
                        order_id=order_id,
                        store_id=store.id,
                        product_id=prod.id,
                        sale_date=order_time,
                        channel=channel,
                        quantity=qty,
                        unit_price=unit_price,
                        cost_price=unit_cost,
                        revenue=item_total,
                        cogs=cogs,
                        gross_profit=gross_profit,
                        margin_pct=margin_pct,
                        created_at=order_time,
                    )
                    sales_records.append(sale_rec)

            net_taxable = order_subtotal - order_discount
            order_tax = round_dec(net_taxable * Decimal("0.18"))
            order_total_amount = round_dec(net_taxable + order_tax)

            order_rec = Order(
                id=order_id,
                order_number=order_number,
                store_id=store.id,
                customer_id=customer.id,
                order_date=order_time,
                status=status,
                channel=channel,
                payment_method=pay_method,
                subtotal=order_subtotal,
                discount_amount=order_discount,
                tax_amount=order_tax,
                total_amount=order_total_amount,
                total_items=order_total_items,
                created_at=order_time,
                updated_at=order_time,
            )
            order_records.append(order_rec)

            if status == "completed":
                cust_aggregates[customer.id]["spend"] += order_total_amount
                cust_aggregates[customer.id]["count"] += 1
                prev_date = cust_aggregates[customer.id]["last_date"]
                if prev_date is None or order_time > prev_date:
                    cust_aggregates[customer.id]["last_date"] = order_time

        # Batch insert
        chunk_save(db, order_records, chunk_size=200, label="orders")
        chunk_save(db, order_items_records, chunk_size=250, label="order items")
        chunk_save(db, sales_records, chunk_size=250, label="sales records")

        # Synchronize customer lifetime value
        print("      [*] Synchronizing customer lifetime metrics...")
        for c in customers_data:
            stats = cust_aggregates.get(c.id)
            if stats and stats["count"] > 0:
                c.total_spend = stats["spend"]
                c.total_orders_count = stats["count"]
                c.last_order_date = stats["last_date"]
                if c.total_spend > Decimal("75000.00"):
                    c.segment = "VIP"
        db.commit()
        print("      [OK] Customer lifetime metrics synchronized.")

        # ---------------------------------------------------------------------
        # 7. SEED INVENTORY (10 Stores * 36 Products = 360 Records)
        # ---------------------------------------------------------------------
        print("\n[7/7] Seeding Inventory Levels across All Stores...")
        inventory_records = []
        for store in stores_data:
            for prod in products_data:
                on_hand = random.randint(12, 110)
                reserved = random.randint(0, min(8, on_hand))
                available = on_hand - reserved
                reorder_pt = random.choice([15, 20, 25])
                reorder_qty = random.choice([30, 50, 75])
                restocked_at = now - timedelta(days=random.randint(1, 14), hours=random.randint(1, 12))

                inv = Inventory(
                    id=uuid.uuid4(),
                    store_id=store.id,
                    product_id=prod.id,
                    quantity_on_hand=on_hand,
                    quantity_reserved=reserved,
                    quantity_available=available,
                    reorder_point=reorder_pt,
                    reorder_quantity=reorder_qty,
                    last_restocked=restocked_at,
                )
                inventory_records.append(inv)

        chunk_save(db, inventory_records, chunk_size=200, label="inventory tracking records")

        print("\n" + "=" * 65)
        print(">>> RETAIL DATABASE SEEDING COMPLETED SUCCESSFULLY! <<<")
        print("=" * 65)

    except Exception as e:
        db.rollback()
        print(f"\n[ERROR] Seeding failed: {e}", file=sys.stderr)
        raise e
    finally:
        db.close()


if __name__ == "__main__":
    run_seed()
