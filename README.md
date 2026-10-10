# Retail KPI Intelligence Platform

> **A full-stack, geospatial retail analytics engine and decision-support system built with React, FastAPI, PostgreSQL, PostGIS, Redis, Scikit-learn, Prophet, and LangGraph.**

---

## Table of Contents
1. [Project Overview & Engineering Highlights](#1-project-overview--engineering-highlights)
2. [Architecture Diagram & Data Flow](#2-architecture-diagram--data-flow)
3. [System Architecture](#3-system-architecture)
4. [Database Architecture & Schema Design](#4-database-architecture--schema-design)
5. [API Documentation & Error Contracts](#5-api-documentation--error-contracts)
6. [AI Agent Architecture (LangGraph + Deterministic Tool Calling)](#6-ai-agent-architecture-langgraph--deterministic-tool-calling)
7. [Machine Learning & Time-Series Forecasting Pipeline](#7-machine-learning--time-series-forecasting-pipeline)
8. [Caching & Performance Layer (Redis + Direct DB Fallback)](#8-caching--performance-layer-redis--direct-db-fallback)
9. [Deployment Architecture](#9-deployment-architecture)
10. [Local Setup Instructions (100% Native & Self-Contained)](#10-local-setup-instructions-100-native--self-contained)
11. [Environment Variables Reference](#11-environment-variables-reference)
12. [Portfolio Screenshots Checklist](#12-portfolio-screenshots-checklist)
13. [Live Recruiter Demo Flow (5-Minute Script)](#13-live-recruiter-demo-flow-5-minute-script)
14. [Technical Interview Questions & Deep-Dive Answers](#14-technical-interview-questions--deep-dive-answers)

---

## 1. Project Overview & Engineering Highlights

The **Retail KPI Intelligence Platform** is an enterprise-grade analytics dashboard designed to solve the common operational gap in retail: aggregating transactional sales records, inventory levels, and store geographic footprints into actionable metrics without relying on third-party black-box SaaS services.

The platform is designed to run **completely locally and natively** on a realistic retail dataset (covering multiple store locations in Hyderabad, Visakhapatnam, Vijayawada, and Guntur, 12+ months of daily sales, customer cohorts, and product inventories).

### Key Engineering Achievements:
- **Zero Mock / Fake Data**: All KPIs, Pareto classifications, time series, geographic calculations, and agent answers are computed in real time from SQL tables and scikit-learn/Prophet models.
- **Geospatial Processing with PostGIS**: True spherical geospatial queries using PostGIS `GEOMETRY(Point, 4326)`, computing store distances and spatial radius aggregations via `ST_Distance` and `ST_DWithin`.
- **Governed AI Agent with LangGraph**: LLM interactions are strictly restricted to tool calls with validated schemas. The agent has **no arbitrary SQL execution access**, preventing prompt injection data leakage.
- **Resilient Offline Architecture**: If Redis is offline or the Gemini API key is omitted, the application degrades gracefully to PostgreSQL queries and a rule-based analytical engine.
- **High Test Fidelity**: 29 Backend integration/unit tests (`pytest`) and 11 Frontend tests (`vitest` + React Testing Library) testing auth, concurrency, PostGIS, forecasting, and caching.

---

## 2. Architecture Diagram & Data Flow

```
                                  +-------------------------------------------------------------+
                                  |                     CLIENT LAYER (SPA)                      |
                                  |  - React 19 + Vite 6 + Tailwind CSS v4                      |
                                  |  - React-Leaflet / OpenStreetMap (Native Map Rendering)     |
                                  |  - Recharts (Time-series, Pareto ABC, KPI Trends)          |
                                  |  - Axios Interceptors (JWT Bearer Injection & Expire Catch) |
                                  +------------------------------+------------------------------+
                                                                 |
                                                                 | HTTPS / JSON (REST)
                                                                 v
                                  +-------------------------------------------------------------+
                                  |                APPLICATION LAYER (FastAPI)                  |
                                  |  - Uvicorn ASGI Server (Multi-worker Async Loop)            |
                                  |  - Pydantic v2 Input Clamping & Response Serialization      |
                                  |  - JWT Authentication Middleware (Passlib + Bcrypt)         |
                                  |  - Structured Logging & Global Error Handlers               |
                                  +--------+--------------------+----------------------+--------+
                                           |                    |                      |
                 +-------------------------+                    |                      +-------------------------+
                 | Cache Read / Write                           | Direct Query                                   | Invocation
                 v                                              v                                                v
+----------------------------------+          +----------------------------------+             +----------------------------------+
|      REDIS CACHING LAYER         |          |       DATABASE & POSTGIS         |             |        AI & ML PIPELINES         |
|  - Deterministic SHA-256 Keys    |          |  - PostgreSQL 16 (Relational DB) |             |  - Meta Prophet (Time-series)    |
|  - TTL Policies (5m - 24h)       | <------+ |  - PostGIS Spatial Extension     | <---------+ |  - Scikit-learn (Pareto & Stats) |
|  - Invalidation on Mutation      |          |  - SQLAlchemy 2.0 Engine & Pool  |             |  - LangGraph State Machine       |
|  - Non-blocking Fallback         |          |  - Spatial GiST & B-Tree Indexes |             |  - Gemini 2.5 Flash Tool Caller  |
+----------------------------------+          +----------------------------------+             +----------------------------------+
```

### Data Flow Walkthrough:
1. **User Request**: The React SPA sends an authenticated request with a JWT `Bearer <token>` to the FastAPI backend.
2. **Authentication & Validation**: Dependency injection validates the token signature and claims (`get_current_user`). Request parameters (dates, horizons, pagination) are clamped via Pydantic.
3. **Cache Evaluation**: The cache manager hashes route arguments into a deterministic key (`kpi:overview:...`). If cached, data returns in `<2ms`.
4. **Database Execution**: On cache miss, SQLAlchemy executes an optimized SQL query against PostgreSQL with connection pooling (`pool_pre_ping=True`, `pool_recycle=300`).
5. **Geospatial & ML Layer**: Geographic queries utilize native PostGIS functions (`ST_X`, `ST_Y`, `ST_Distance`). Time-series forecasts pull historical sales, fit a Prophet model, and return projection curves with lower/upper uncertainty intervals.
6. **AI Agent Tool Calling**: When chatting with the AI Analyst, user intent is parsed by LangGraph, mapped to a verified Python tool, queried against the database, and formatted into structured findings.

---

## 3. System Architecture

### Frontend Architecture
- **Framework**: React 19 bootstrapped with Vite 6.
- **Routing**: React Router v7 with protected route wrappers (`ProtectedRoute.jsx`) that verify authentication state before rendering private dashboards.
- **Styling**: Tailwind CSS v4 using responsive flex/grid layouts.
- **Mapping**: Leaflet 1.9 and React-Leaflet 5 rendering OpenStreetMap tiles without proprietary external map APIs.
- **Charts**: Recharts 3 responsive SVG containers displaying revenue trends, profit margins, ABC inventory distributions, and store comparisons.
- **API Client**: Axios instance configured with request interceptors (JWT injection) and response interceptors (automatic token revocation on `401`).

### Backend Architecture
- **Framework**: FastAPI (Python 3.12) running under Uvicorn.
- **Architecture Pattern**: Layered Service-Repository Pattern:
  - `app/api/v1/`: API endpoints, route definitions, and HTTP status codes.
  - `app/services/`: Pure business logic, aggregations, and ML wrappers.
  - `app/models/`: SQLAlchemy 2.0 declarative database entities.
  - `app/schemas/`: Pydantic v2 schemas for request validation and response filtering.
  - `app/core/`: Configuration via `pydantic-settings`, JWT cryptography, and caching manager.

---

## 4. Database Architecture & Schema Design

The schema is normalized to 3NF with appropriate indexing, foreign key constraints, and PostGIS geographic types.

```
+--------------------+        +--------------------+        +---------------------+
|       Store        |        |      Product       |        |      Category       |
+--------------------+        +--------------------+        +---------------------+
| id (PK, UUID)      |        | id (PK, UUID)      |        | id (PK, UUID)       |
| code (Unique)      |        | sku (Unique)       |        | name (VarChar)      |
| name (VarChar)     |        | name (VarChar)     |        | code (Unique)       |
| city (VarChar)     |        | category_id (FK) --+------> | description         |
| location (Geometry)|        | cost_price (Num)   |        +---------------------+
| is_active (Bool)   |        | selling_price (Num)|
+---------+----------+        +---------+----------+
          |                             |
          |                             |
          v                             v
+--------------------+        +--------------------+        +---------------------+
|     Inventory      |        |     OrderItem      |        |      Customer       |
+--------------------+        +--------------------+        +---------------------+
| id (PK, UUID)      |        | id (PK, UUID)      |        | id (PK, UUID)       |
| store_id (FK)      |        | order_id (FK)      |        | email (Unique)      |
| product_id (FK)    |        | product_id (FK)    |        | name (VarChar)      |
| quantity (Int)     |        | quantity (Int)     |        | city (VarChar)      |
| reorder_level (Int)|        | unit_price (Num)   |        | segment (VarChar)   |
+--------------------+        | subtotal (Num)     |        +----------+----------+
                              +---------+----------+                   |
                                        |                              |
                                        v                              |
                              +--------------------+                   |
                              |       Order        |                   |
                              +--------------------+                   |
                              | id (PK, UUID)      |                   |
                              | order_number (UQ)  |                   |
                              | customer_id (FK) <-+-------------------+
                              | store_id (FK)      |
                              | total_amount (Num) |
                              | order_date (Date)  |
                              +--------------------+
```

### Key Database Engineering Decisions:
1. **PostGIS Point Geometry**:
   ```python
   location = Column(Geometry(geometry_type="POINT", srid=4326), nullable=False)
   ```
   Stores longitude and latitude as spherical coordinates (WGS 84). Indexed with a **GiST spatial index** (`idx_stores_location_gist`) to allow sub-millisecond geographic proximity searches.
2. **Numeric Precision**: Currency amounts (`cost_price`, `selling_price`, `total_amount`, `profit`) use `NUMERIC(12, 2)` to eliminate floating-point rounding errors.
3. **Compound & Performance Indexes**:
   - `idx_orders_store_date`: Compound index on `(store_id, order_date)` for fast range queries.
   - `idx_order_items_order_prod`: Foreign key composite index.
   - `idx_inventory_store_prod`: Unique constraint preventing duplicate inventory rows.

---

## 5. API Documentation & Error Contracts

All endpoints are versioned under `/api/v1` and document schemas automatically at `/docs` (OpenAPI 3.1).

### Key Endpoints:
| Method | Route | Description | Auth Required |
| :--- | :--- | :--- | :---: |
| `POST` | `/api/v1/auth/login` | Authenticates user; returns JWT bearer token | No |
| `POST` | `/api/v1/auth/register` | Registers new administrator or manager | No |
| `GET` | `/api/v1/auth/me` | Returns current user profile and role | Yes |
| `GET` | `/api/v1/dashboard/overview` | Core KPIs (Revenue, Profit, Orders, Margin, AOV) | Yes |
| `GET` | `/api/v1/dashboard/sales-trend` | Daily/weekly aggregated revenue and order curves | Yes |
| `GET` | `/api/v1/stores` | Store listing with PostGIS coordinates | Yes |
| `GET` | `/api/v1/stores/nearby` | Geospatial query: finds stores within radius | Yes |
| `GET` | `/api/v1/analytics/pareto` | ABC classification of inventory and products | Yes |
| `GET` | `/api/v1/forecast/sales` | Prophet time-series sales projection | Yes |
| `POST` | `/api/v1/agent/chat` | AI Retail Analyst conversational endpoint | Yes |
| `GET` | `/api/v1/health` | Diagnostic status of DB, PostGIS, and Redis | No |

### Standardized Error Contract:
FastAPI exception handlers enforce a consistent JSON structure across 400, 401, 403, 422, and 500 responses:
```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Request payload validation failed.",
    "details": [
      {
        "loc": ["query", "horizon_days"],
        "msg": "Input should be greater than or equal to 1",
        "type": "greater_than_equal"
      }
    ]
  },
  "detail": "Input should be greater than or equal to 1"
}
```

---

## 6. AI Agent Architecture (LangGraph + Deterministic Tool Calling)

The AI Analyst is designed around **strict deterministic guardrails**: the LLM does not generate SQL directly and cannot access table structures. It acts solely as an intent-parsing and tool-invoking orchestrator.

```
User Query: "Which store had the highest revenue last month?"
                     |
                     v
       FastAPI Input Clamping (Max 1,000 chars)
                     |
                     v
          LangGraph StateGraph Node
                     |
                     v
   LLM Function Calling (Gemini 2.5 Flash)
        Tool Selected: get_store_performance(metric='revenue', limit=5)
                     |
                     v
   Backend Tool Execution (Direct SQLAlchemy Aggregation)
        Returns: [{"store": "Hyderabad Flagship", "revenue": 142500.00}, ...]
                     |
                     v
   Final Synthesis & Grounded Response (Distinguishes facts from advice)
```

### Registered Tools:
1. `get_sales_kpi`: Retrieves company revenue, profit, orders, and average ticket size.
2. `get_store_performance`: Ranks stores by revenue or profit margin with bounded limits ($1 \le n \le 50$).
3. `get_product_performance`: Identifies top-performing and underperforming SKUs.
4. `get_customer_metrics`: Aggregates customer lifetime values, retention rates, and cohort metrics.
5. `get_sales_trend`: Extracts historical daily revenue series.
6. `compare_stores`: Computes head-to-head metrics between two specific store IDs.
7. `compare_periods`: Calculates percentage variance between two calendar windows.

### Safe Fallback Mode:
If `GEMINI_API_KEY` is not provided or the network is offline, the agent router activates a **rule-based analytical parser**. It regex-identifies user intents (e.g., "highest revenue", "compare", "forecast") and executes the exact same underlying Python tools, returning verified metrics without external API dependence.

---

## 7. Machine Learning & Time-Series Forecasting Pipeline

### Prophet Time-Series Model
- **Target Variable**: Aggregate daily gross sales revenue ($y$) over time ($ds$).
- **Features Included**:
  - Additive trend with changepoints.
  - Weekly seasonality (capturing retail weekend peaks vs. weekday troughs).
  - Monthly/yearly seasonality.
- **Uncertainty Estimation**: 80% confidence interval bands (`yhat_lower`, `yhat_upper`) generated via Monte Carlo simulation.
- **Cold-Start Handling**: If historical sales data contains fewer than 14 records, the service gracefully returns historical rolling averages rather than crashing on under-specified model fits.
- **Leakage Prevention**: Feature scaling and date sorting are strictly chronologically ordered. Test horizons do not overlap with historical training datasets.

---

## 8. Caching & Performance Layer (Redis + Direct DB Fallback)

1. **Deterministic Key Generation**:
   Keys are generated by combining the namespace, sorted query parameters, and a SHA-256 hash of complex filters:
   `kpi:overview:store_12:start_2026-01-01:end_2026-06-30`
2. **TTL Strategy**:
   - Dashboard Overview: 300 seconds (5 minutes)
   - Store & Product Performance: 600 seconds (10 minutes)
   - Forecasting Models: 3600 seconds (1 hour)
3. **Resilient Non-Blocking Fallback**:
   The caching layer wraps `redis.Redis` in a singleton class with a 15-second reconnection cooldown. If Redis crashes or is uninstalled, it logs an alert and routes all traffic directly to PostgreSQL with **zero dropped requests**.

---

## 9. Deployment Architecture

The system can be deployed in two configurations:

### Option A: Local / Self-Hosted (100% Free & Self-Contained)
Runs via Docker Compose or native virtual environment:
- **Database**: PostgreSQL 16 Alpine + PostGIS 3.4
- **Cache**: Redis 7 Alpine
- **Backend**: FastAPI on Python 3.12 Slim
- **Frontend**: Nginx Alpine serving pre-compiled React 19 bundle

### Option B: Cloud Production (Zero-Cost Free Tiers)
- **Frontend**: Vercel (Edge CDN, SSL, continuous Git deployment)
- **Backend**: Render Web Service (Docker runtime, auto-healthchecks)
- **Database**: Supabase PostgreSQL (Includes native PostGIS extension)
- **Cache**: Upstash Serverless Redis (Native TLS `rediss://`)

---

## 10. Local Setup Instructions (100% Native & Self-Contained)

### Prerequisites:
- Python 3.12+
- Node.js 20+ and npm
- PostgreSQL 15+ with PostGIS extension installed (or use Docker)
- Redis (optional; system falls back gracefully to DB if not running)

### Step 1: Clone & Configure Backend
```powershell
cd d:\retail-kpi\backend

# Create virtual environment
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your local PostgreSQL credentials:
# DATABASE_URL=postgresql://postgres:postgres@localhost:5432/retail_kpi
```

### Step 2: Initialize Database & Seed Realistic Data
```powershell
# Run Alembic migrations to build tables and spatial geometries
alembic upgrade head

# Seed 12+ months of consistent retail data (stores, products, sales, inventory)
python scripts\seed_db.py
```

### Step 3: Run Backend Server
```powershell
uvicorn app.main:app --reload --port 8000
```
- API Base: `http://localhost:8000`
- Swagger UI: `http://localhost:8000/docs`
- Healthcheck: `http://localhost:8000/health`

### Step 4: Run Frontend Client
```powershell
# Open a new terminal
cd d:\retail-kpi\frontend

# Install dependencies
npm install

# Start Vite dev server
npm run dev
```
- Frontend UI: `http://localhost:5173`
- Pre-seeded Admin Credentials:
  - **Email**: `admin@retailkpi.com`
  - **Password**: `Admin@123456`

### Step 5: Run Automated Tests
```powershell
# Run 29 Backend Tests
cd d:\retail-kpi
backend\venv\Scripts\pytest backend\tests -v

# Run 11 Frontend Tests
cd d:\retail-kpi\frontend
npm test
```

---

## 11. Environment Variables Reference

| Variable | Type | Default | Description |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | string | `development` | Environment mode (`development` / `production`). |
| `DEBUG` | boolean | `true` | When `false`, suppresses internal stack traces in JSON errors. |
| `DATABASE_URL` | string | `postgresql://...` | PostgreSQL connection URI. Automatically converts `postgres://` to `postgresql://`. |
| `REDIS_URL` | string | `redis://localhost:6379/0` | Redis URI. Supports `rediss://` for Upstash cloud TLS. |
| `SECRET_KEY` | string | *(pre-set)* | 64-character hex key used for signing session tokens. |
| `JWT_SECRET` | string | *(pre-set)* | 64-character hex key used for signing JWT access tokens. |
| `JWT_ALGORITHM` | string | `HS256` | JWT signing algorithm. |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | int | `1440` | Token validity window (24 hours). |
| `GEMINI_API_KEY` | string | `""` | Google Gemini API key. If empty, triggers local analytical fallback. |
| `CORS_ORIGINS` | string | `http://localhost:5173...`| Comma-separated list of allowed CORS client origins. |
| `VITE_API_URL` | string | `http://localhost:8000/api`| Target API endpoint for frontend HTTP clients. |

---

## 12. Portfolio Screenshots Checklist

For documenting this project in a portfolio or technical blog post, capture the following views:

1. **Executive Dashboard (`/dashboard`)**:
   - Shows top KPI metric cards (Total Revenue, Gross Profit, Total Orders, Average Order Value).
   - Dynamic date-range picker and store filter bar.
   - Revenue and profit trend charts side-by-side.
2. **Interactive Geographic Map (`/stores`)**:
   - Leaflet map displaying store location pins across Hyderabad, Visakhapatnam, and Vijayawada.
   - Store popup card showing individual store revenue, manager contact, and active inventory status.
3. **Inventory & Product Performance (`/products`)**:
   - Pareto ABC inventory classification chart (Class A: 80% revenue drivers).
   - Product table with low-stock badges and category tags.
4. **Sales Forecasting Engine (`/analytics`)**:
   - Recharts visual displaying historical sales curve transitioning into a 30-day Prophet forecast.
   - Upper and lower confidence interval bands highlighted.
5. **AI Retail Analyst Chat (`/agent`)**:
   - User asking: *"Which store generated the highest revenue?"*
   - UI displaying tool execution badge (`get_store_performance`) and formatted data table response.
6. **API Documentation (`/docs`)**:
   - Swagger UI showing clean grouping of Auth, Dashboard, Stores, Analytics, and Agent routes.

---

## 13. Live Recruiter Demo Flow (5-Minute Script)

- **Minute 0:00 - 1:00 (The Problem & Solution)**:
  *"Most retail dashboards either present static mock data or rely on heavy, expensive third-party BI software. I engineered this platform from scratch to demonstrate a production-ready, full-stack analytical architecture where every metric is calculated live from a PostGIS-enabled PostgreSQL database."*
- **Minute 1:00 - 2:00 (Executive KPIs & Caching)**:
  - Log in as `admin@retailkpi.com`.
  - Open Developer Tools Network tab.
  - Load `/dashboard`. Show initial response time (`~120ms` SQL aggregation).
  - Refresh or change date range. Show Redis cache hit serving the identical calculation in `<4ms`.
- **Minute 2:00 - 3:00 (Geospatial PostGIS Capabilities)**:
  - Navigate to the **Stores** tab.
  - Explain that coordinates are stored as native PostGIS spatial points (`GEOMETRY(Point, 4326)`).
  - Click on a store marker in Hyderabad to reveal its real-time profit and sales volume calculated through spatial database joins.
- **Minute 3:00 - 4:00 (Forecasting & Pareto Analytics)**:
  - Open the **Analytics** view.
  - Showcase the Pareto ABC product distribution chart.
  - Demonstrate the Prophet 30-day sales forecast, explaining that the time-series model accounts for retail weekend seasonality and produces genuine confidence intervals.
- **Minute 4:00 - 5:00 (Grounded AI Agent & Architectural Safety)**:
  - Navigate to the **AI Analyst** view.
  - Type: *"Compare the performance between Hyderabad and Vizag stores."*
  - Point out the `compare_stores` tool badge, demonstrating that the LLM has zero arbitrary SQL execution access and can only invoke strongly-typed Python functions.
  - Show the 40 passing tests (`29 pytest`, `11 vitest`) to highlight software engineering rigor.

---

## 14. Technical Interview Questions & Deep-Dive Answers

### Q1: Why use PostGIS instead of simply storing latitude and longitude as two separate float columns?
> **Answer**: Storing coordinates as floats (`lat`, `lng`) works for basic point-lookup display, but fails when executing spatial operations. A standard Cartesian distance calculation ($\sqrt{\Delta x^2 + \Delta y^2}$) does not account for the curvature of the Earth, resulting in severe distortion over medium and long distances. PostGIS provides the `GEOMETRY(Point, 4326)` type and spatial indexing via **GiST (Generalized Search Tree)**. GiST indexes divide the globe into hierarchical bounding boxes, allowing the database to execute bounding-box filters and spatial queries (`ST_DWithin`, `ST_Distance`) in logarithmic $O(\log N)$ time rather than conducting full $O(N)$ table scans.

### Q2: How did you prevent SQL injection and hallucinations in the AI Analyst?
> **Answer**: I completely avoided "Text-to-SQL" architectures where an LLM writes raw SQL queries. That approach exposes the database to prompt injections, schema leaks, and query execution timeouts. Instead, I used **LangGraph with strongly-typed tool calling**. The LLM is provided only with a schema of 7 pre-defined analytical functions (e.g., `get_sales_kpi`, `compare_stores`). The LLM selects the tool and extracts arguments; the backend then clamps parameters (e.g., bounding horizons between 1 and 90 days) and executes parameterized SQLAlchemy queries. The model only receives structured JSON outputs to synthesize its answer.

### Q3: How do you handle database connection pooling when running FastAPI with multiple worker processes?
> **Answer**: When running multiple Uvicorn workers, each worker runs in its own operating system process with an isolated memory space. If each worker opened unbounded connections, it could quickly exhaust PostgreSQL's `max_connections`. In `app/database.py`, I configured SQLAlchemy's `create_engine` with `pool_size=10`, `max_overflow=20`, `pool_recycle=300`, and `pool_pre_ping=True`. `pool_pre_ping` issues a lightweight `SELECT 1` ping before handing a checked-out connection to the request handler, ensuring severed connections (e.g., cloud network timeouts) are recycled without throwing 500 errors to users.

### Q4: What happens if Redis crashes in production? Does the whole application go down?
> **Answer**: No. I implemented a resilient singleton `RedisCacheManager`. Every cache read/write is wrapped in exception guards. If Redis fails to respond or is offline, the manager catches the connection error, logs a structured warning, records the timestamp, and initiates a 15-second non-blocking cooldown. The service layer immediately bypasses the cache and executes the live SQLAlchemy query directly against PostgreSQL. The platform transitions seamlessly between cached mode and direct-query fallback mode with zero downtime or broken API responses.

### Q5: How did you prevent data leakage in your sales forecasting model?
> **Answer**: In time-series forecasting, data leakage occurs if future values inadvertently influence past features (e.g., global mean imputation, seasonal indicators computed across the entire historical and test horizons, or improper train/test splitting). To prevent this, time-series splits are strictly chronological. Any rolling aggregations or seasonal baselines are computed strictly within the historical window ($t \le T_0$) prior to generating projections for future timestamps ($t > T_0$).

---

## License
MIT License. Developed for software engineering demonstration and technical portfolio review.
