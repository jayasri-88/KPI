# Retail KPI Intelligence Platform — Engineering Portfolio Documentation

This document serves as an exhaustive technical portfolio breakdown and engineering review for software engineering interviews, architectural audits, and resume evaluation.

---

## 1. Resume Summary & Bullet Points

### Full-Stack / Backend Software Engineer
- **Architected and delivered** a full-stack retail intelligence platform using **FastAPI**, **PostgreSQL/PostGIS**, **SQLAlchemy 2.0**, and **React 19**, processing multi-store transactional datasets with zero reliance on paid black-box APIs.
- **Implemented geospatial store analytics** using PostGIS `GEOMETRY(Point, 4326)` and **GiST spatial indexing**, enabling sub-millisecond distance computations and radius filtering.
- **Engineered an autonomous AI Retail Analyst** using **LangGraph** and function calling; established strict architectural safety boundaries eliminating raw Text-to-SQL generation and enforcing parameterized tool execution.
- **Built time-series sales forecasting pipelines** with **Meta Prophet** and **Scikit-learn**, incorporating weekly and holiday seasonality, uncertainty intervals, and historical rolling average fallbacks.
- **Developed a fault-tolerant Redis caching layer** with deterministic hashing and automated 15-second non-blocking cooldown fallback to direct PostgreSQL queries upon cache disconnects.
- **Established an enterprise testing layer** with 40 automated test suites across **pytest** and **Vitest** (React Testing Library), achieving 100% pass rates across auth, spatial queries, forecasting, and agent error boundaries.

---

## 2. Core Technology Stack Matrix

| Layer | Technologies Selected | Justification / Engineering Rationale |
| :--- | :--- | :--- |
| **Frontend** | React 19, Vite 6, Tailwind CSS v4 | Rapid client-side rendering, tree-shaken production bundles (`~302 kB` gzip), responsive executive layout. |
| **Data Viz** | Recharts 3, Leaflet / React-Leaflet 5 | Native SVG charting for trends and Pareto distributions; OpenStreetMap tiles without proprietary API keys. |
| **Backend API** | FastAPI, Uvicorn, Pydantic v2 | High-throughput asynchronous ASGI server, automatic OpenAPI 3.1 docs, strict schema validation and parameter clamping. |
| **Database** | PostgreSQL 16 + PostGIS Extension | ACID transactions, spherical geospatial indexing (`ST_Distance`, `ST_DWithin`), 3NF schema design. |
| **ORM** | SQLAlchemy 2.0 (Modern Declarative) | Robust session management, connection pooling (`pool_pre_ping=True`), explicit type mapping (`Numeric(12, 2)`). |
| **Cache** | Redis 7 + Graceful Fallback | In-memory key-value caching with deterministic keys; zero-latency database fallback if Redis is unreachable. |
| **AI / Orchestration** | LangGraph, Gemini 2.5 Flash, Regex Fallback | Deterministic tool calling with zero SQL injection risk; offline analytical fallback when API keys are absent. |
| **ML & Analytics** | Meta Prophet, Scikit-learn, Pandas, NumPy | Additive time-series modeling with 80% confidence bands; Pareto ABC revenue classification. |
| **DevOps & QA** | Docker, Docker Compose, Pytest, Vitest | Multi-container local orchestration, multi-stage Nginx Alpine builds, and automated unit/integration test suites. |

---

## 3. Database Schema Specification

### Tables & Relationships
1. **`users`**: Manages RBAC authentication (`id`, `email`, `hashed_password`, `role`, `created_at`). Passwords hashed with bcrypt (12 rounds).
2. **`categories`**: Product classifications (`id`, `name`, `code`, `description`).
3. **`products`**: Catalog items (`id`, `sku`, `name`, `category_id`, `cost_price`, `selling_price`, `is_active`). Enforces `cost_price <= selling_price` check constraint.
4. **`stores`**: Physical retail locations (`id`, `code`, `name`, `city`, `location`, `is_active`). Coordinates stored as `GEOMETRY(Point, 4326)` with a GiST index.
5. **`inventory`**: Store stock levels (`id`, `store_id`, `product_id`, `quantity`, `reorder_level`, `updated_at`). Unique constraint on `(store_id, product_id)`.
6. **`customers`**: Profiles and cohorts (`id`, `name`, `email`, `phone`, `city`, `segment`).
7. **`orders`**: Transaction header records (`id`, `order_number`, `customer_id`, `store_id`, `order_date`, `total_amount`, `status`). Compound index on `(store_id, order_date)`.
8. **`order_items`**: Line items (`id`, `order_id`, `product_id`, `quantity`, `unit_price`, `subtotal`).
9. **`sales`**: Denormalized analytical ledger (`id`, `order_id`, `store_id`, `product_id`, `sale_date`, `revenue`, `cost`, `profit`).

---

## 4. Verification & Testing Evidence

All tests pass against live PostgreSQL instances, PostGIS functions, and test data:

- **Backend Pytest Suite**: 29 passed in 45.89s
  - `test_auth.py`: 7 tests
  - `test_database.py`: 4 tests
  - `test_kpi_dashboard.py`: 5 tests
  - `test_analytics_and_forecasting.py`: 5 tests
  - `test_ai_agent_tools.py`: 8 tests
- **Frontend Vitest Suite**: 11 passed in 3.92s
  - `api_integration.test.js`: 4 tests
  - `auth_flow.test.jsx`: 4 tests
  - `MetricCard.test.jsx`: 3 tests
- **Total Test Coverage**: 40 unit and integration tests verifying real analytical queries and edge cases.
