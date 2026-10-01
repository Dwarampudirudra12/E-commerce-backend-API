# E-Commerce Backend API — Milestones 1–4

M1: Dockerised FastAPI + Postgres + Redis, 25-table schema via Alembic,
JWT auth + RBAC (4 roles), versioned API + Swagger.
M2: Catalog/search, cart, idempotent checkout (atomic stock, no oversell),
test-mode payments + signed webhooks, fraud baseline.
M3: Tuned fraud (ROC-AUC 0.96) + review queue, demand forecasts, recommendations,
notifications, analytics + React dashboard, Grafana alerts.
M4: 84% test coverage, rate limiting, Locust report, CI, prod compose, docs.

## Quickstart (one command — M1 criterion #1)

```powershell
Copy-Item .env.example .env
docker compose up --build
# API: http://localhost:8000/docs | Health: http://localhost:8000/health/live
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
```

Demo logins (`Password123!`): `customer@example.com`, `seller@example.com`,
`support@example.com`, `admin@example.com`.

## Local (no Docker) test

```powershell
pip install -r requirements.txt
pytest -q
```

## API conventions
* Versioned: `/api/v1/...` (health unversioned). Errors: `{detail, code, request_id?}`.
* Pagination: `?page=1&page_size=20` → `{items, total, page, page_size}`.
* Auth: `Authorization: Bearer <access>`; refresh rotation at `POST /api/v1/auth/refresh`.

## Docs
* `docs/API_SPEC.md` — endpoint catalogue + RBAC matrix
* `docs/ER_DIAGRAM.md` — Mermaid ER + table list
* `docs/ARCHITECTURE.md` — module boundaries + branching
* `docs/USER_MANUAL.md` — per-role quick paths
* `docs/DEPLOYMENT.md` — AWS reference + prod checklist
* `docs/SECURITY.md` — OWASP review + secrets audit
* `docs/LOAD_TEST_REPORT.md` — measured 200-user numbers
* `docs/PRESENTATION.md` — 8-minute demo script
* Swagger: `/docs`, ReDoc: `/redoc`, OpenAPI: `/openapi.json`

## Load test (M4)
```powershell
pip install locust
docker compose exec api python scripts/seed_load.py
locust -f load/locustfile.py --headless -u 200 -r 20 --run-time 90s --host http://localhost:8000
```

## Frontend (React + Vite + Tailwind)
```powershell
cd frontend
Copy-Item .env.example .env   # VITE_API_BASE_URL, default http://localhost:8000
npm install
npm run dev                  # http://localhost:5173
npm run build                # production bundle
```
Dark-glassmorphism storefront + seller/support/admin consoles, fraud
intelligence, forecasting, analytics, notifications and system monitoring —
see `frontend/README.md`. JWT auth with refresh, RBAC route guards mirroring
the backend matrix (backend remains the security authority).
