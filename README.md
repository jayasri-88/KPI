# Retail KPI Intelligence Platform

Full-stack retail analytics platform: a FastAPI + PostgreSQL backend serving KPI and
analytics APIs, and a React 19 + Vite dashboard consuming them.

```
┌────────────────────┐        /api/* (Vite dev proxy)       ┌──────────────────────┐
│  React 19 + Vite   │ ───────────────────────────────────▶ │  FastAPI backend     │
│  localhost:5173    │                                      │  localhost:8000      │
└────────────────────┘                                      └──────────┬───────────┘
                                                                       │ SQLAlchemy
                                                            ┌──────────▼───────────┐
                                                            │ PostgreSQL (Neon or  │
                                                            │ local)  ◀── ingest   │
                                                            └──────────▲───────────┘
                                                                       │
                                                            ┌──────────┴───────────┐
                                                            │  data/*.csv          │
                                                            └──────────────────────┘
```

## Repository layout

```
backend/
  app/
    main.py               FastAPI app, router registration, /health
    database.py           Engine, session factory, init_db()
    models.py             SQLAlchemy models (9 tables)
    schemas.py            Pydantic request/response schemas
    api/                  Routers: auth, dashboard, analytics, stores,
                          products, customers, orders, inventory, sku
    services/             Query logic: dashboard_service, analytics_service,
                          inventory_service
    core/config.py        Settings (pydantic-settings, reads backend/.env)
  scripts/
    ingest_postgres.py    Idempotent CSV → PostgreSQL ingestion
  tests/                  Pytest suite (runs against a throwaway Postgres schema)
frontend/
  src/
    pages/                Dashboard, Analytics, Sales, Stores, Products,
                          Customers, Forecast, Assistant, Auth
    components/           Charts (recharts), metric cards, inventory alerts
    services/api.js       Axios client — every call targets /api/*
  vite.config.js          Dev proxy: /api → http://localhost:8000
data/                     Source CSV datasets (see Ingestion)
```

## Quickstart

### Backend

Requires Python 3.12 and a reachable PostgreSQL database.

```bash
cd backend
python -m venv .venv
.venv/bin/pip install -r requirements.txt   # NOTE: see Known issues — file is UTF-16
```

Create `backend/.env` (gitignored):

```dotenv
DATABASE_URL=postgresql://user:password@host:5432/retail_kpi
JWT_SECRET=change_me
```

Start the API:

```bash
cd backend
.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

- Health check: `GET http://127.0.0.1:8000/health`
- Swagger UI: `http://127.0.0.1:8000/docs`
- On startup the app runs `init_db()`, creating all tables if missing.

### Load the data

```bash
cd backend
.venv/bin/python scripts/ingest_postgres.py
```

The script is idempotent (safe to rerun, resumable after interruption) and logs a
per-entity summary plus a data-quality report. See [Ingestion](#ingestion).

### Frontend

```bash
cd frontend
npm install
npm run dev        # http://localhost:5173
```

The Vite dev server proxies `/api/*` to `http://localhost:8000`, so no CORS or
absolute URLs are needed in development. `npm run build` produces a static bundle.

## Environment variables

| Variable       | Where      | Purpose                                        |
|----------------|------------|------------------------------------------------|
| `DATABASE_URL` | backend/.env | PostgreSQL connection string (default: local `retail_kpi` db) |
| `JWT_SECRET`   | backend/.env | JWT signing secret (default is a placeholder — change it) |
| `JWT_ALGORITHM`, `ACCESS_TOKEN_EXPIRE_MINUTES` | backend/.env | Auth tuning |
| `GEMINI_API_KEY`, `REDIS_URL` | backend/.env | Reserved for future AI/caching features (unused) |

## API surface

All business endpoints are mounted once under `/api/<domain>` (prefix applied at
mount time in `main.py`; routers declare no internal prefix).

| Domain | Endpoints |
|---|---|
| Auth | `POST /api/auth/register` · `POST /api/auth/login` · `GET /api/auth/me` |
| Dashboard | `GET /api/dashboard/overview` · `GET /api/dashboard/summary` |
| Analytics | `GET /api/analytics/sales-trend` · `GET /api/analytics/sku-performance` · `GET /api/analytics/region-performance` · `GET /api/analytics/category-performance` |
| Inventory | `GET /api/inventory/alerts` · `GET /api/inventory/summary` |
| SKU Intelligence | `GET /api/sku/intelligence` |
| Stores / Products / Customers / Orders | CRUD (stores, products, customers) · order + line-item endpoints (`/api/orders`) |

Interactive docs at `/docs` list every route with schemas.

## Ingestion

`backend/scripts/ingest_postgres.py` loads `data/*.csv` into PostgreSQL
(the same `DATABASE_URL` the API reads), making PostgreSQL the source of truth.

| CSV | Rows | Target |
|---|---|---|
| `products.csv` | 80 | `categories` + `products` |
| `retailers.csv` | 120 | `stores` (location stored as WKT `POINT(lon lat)` text) |
| `sales_transactions.csv` | 90,820 | `sales` (fact rows) **and** `orders` + `order_items` (one transaction → one single-line order) |
| `inventory.csv` | 59,217 | `inventory` — **latest snapshot only** per (retailer, product); the schema models current state |
| `monthly_kpis.csv` | 360 | *not loaded* — pre-aggregated cube; the API computes KPIs live |

Design points:

- **Identity**: source business keys (`sku_code`, `retailer_id`, `sale_id`) mapped to
  deterministic UUIDv5s — the same source row always produces the same database row.
- **Idempotency**: every loader is a batched (5,000-row) `INSERT … ON CONFLICT DO UPDATE`
  on that identity. Reruns converge; no truncate-and-reload.
- **Transactions**: one transaction per entity, so an interrupted run leaves consistent
  partial state that the next run completes.
- **Revenue semantics** (verified against the source): `revenue` in the CSV is **gross**
  (`quantity × unit_price`); `discount_amount` = gross − net; `total_revenue` KPI = net.
- **Validation**: nulls, duplicates, invalid dates/prices, unknown FKs and malformed
  coordinates are reported, not silently dropped. The script exits non-zero on failure.
- **Customers**: the source has no customer dimension; `orders.customer_id` is NULL.

## KPI definitions

Implemented in `dashboard_service.py` (documented in its module docstring) and
`analytics_service.py`, and locked down by tests:

| KPI | Definition |
|---|---|
| Revenue | `SUM(order_items.total_price)` (gross) |
| Net revenue | `SUM(total_price × (1 − discount_percent/100))` |
| Units sold | `SUM(order_items.quantity)` |
| Transactions | Count of distinct orders with ≥ 1 line item |
| Average order value | `revenue / transactions` |
| Profit | `SUM(quantity × (unit_price − product.cost_price))` (gross margin) |
| Profit margin | `profit / revenue × 100` |
| Revenue / profit growth | `(last month − previous month) / previous month`, same-month comparison |
| Category / region contribution | Top entity revenue share of total revenue |
| SKU performance | Per-product revenue, units, transactions, profit, margin (category joined by name) |
| Cancelled orders | Excluded from all order-derived KPIs (`status = 'cancelled'`) — documented convention, as no business rule existed in the repo |

All ratio KPIs guard against division by zero and return `null` rather than a fake
value when they cannot be computed.

## Testing

```bash
cd backend
.venv/bin/python -m pytest tests/ -v
```

The suite runs against real PostgreSQL using a throwaway schema created per test
session (application tables are never touched). Fixtures are deterministic and every
assertion checks hand-calculated KPI values — not just HTTP 200s. Covers monthly
grouping, revenue/units/transaction aggregation, cancelled-order exclusion, AOV,
profit, growth, contributions, SKU field mapping, and empty-database stability.

## Known issues / limitations

- `backend/requirements.txt` is UTF-16 encoded, which `pip install -r` rejects
  (`pip install -r <(iconv -f UTF-16 -t UTF-8 backend/requirements.txt)` works around it).
  It is also missing `pandas` and `pytest`.
- Inventory history (older snapshots) is discarded on load; the schema models
  current state only.
- Orders are single-line (1 transaction = 1 order item) because the source data is
  transaction-grain.
- Sales, Forecast and Assistant pages are placeholders awaiting future commits.
- The Neon credentials used during development were shared in chat — rotate before
  any real deployment.
