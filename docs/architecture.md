# System Architecture - Retail KPI Intelligence Platform

```
+-----------------------------------------------------------------------+
|                           CLIENT LAYER                                |
|  React 19 + Vite 6 + Tailwind CSS + Recharts + React-Leaflet          |
+-----------------------------------+-----------------------------------+
                                    |
                                    | REST / JSON (CORS Enabled)
                                    v
+-----------------------------------------------------------------------+
|                         APPLICATION LAYER                             |
|  FastAPI (Python 3.12)                                                |
|  - Uvicorn ASGI Server                                                |
|  - Pydantic v2 Settings & Request/Response Validation                  |
|  - JWT Authentication & RBAC Middleware                               |
|  - Service Layer (Analytics, Dashboard, Stores, Orders, Products)     |
+-------------------+--------------------+------------------------------+
                    |                    |
                    v                    v
+-----------------------+        +--------------------------------------+
|     DATA LAYER        |        |          ANALYTICS & AI LAYER        |
|  - PostgreSQL 16      |        |  - Meta Prophet (Time-series Forecast)
|  - PostGIS Spatial    |        |  - Scikit-learn (Customer RFM)       |
|  - SQLAlchemy 2.0 ORM |        |  - LangGraph + Google Gemini Agent   |
|  - Redis Cache        |        |  - Real-time DB Tool Calling         |
+-----------------------+        +--------------------------------------+
```

## Phase Breakdown
1. **Phase 1: Project Setup + FastAPI + React** [Completed]
2. **Phase 2: PostgreSQL + PostGIS + SQLAlchemy**
3. **Phase 3: Database Models + Migrations + Seed Data**
4. **Phase 4: Authentication + JWT**
5. **Phase 5: Backend REST APIs**
6. **Phase 6: React Dashboard**
7. **Phase 7: Charts + Filters + Tables**
8. **Phase 8: PostGIS + Interactive Map**
9. **Phase 9: ML Analytics + Forecasting**
10. **Phase 10: Gemini + LangGraph AI Agent**
11. **Phase 11: Redis Caching**
12. **Phase 12: Testing + Security + Error Handling**
13. **Phase 13: Docker + Deployment**
14. **Phase 14: README + Architecture + Portfolio Docs**
