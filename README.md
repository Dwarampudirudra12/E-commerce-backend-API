# E-Commerce Backend API — Milestone 1

M1 (Weeks 1-2): init, design, core setup — Dockerised FastAPI + Postgres + Redis,
22-table schema via Alembic, JWT auth + RBAC (4 roles), versioned API + Swagger.

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
* `docs/ER_DIAGRAM.md` — Mermaid ER + 22-table list
* `docs/ARCHITECTURE.md` — module boundaries + branching
* Swagger: `/docs`, ReDoc: `/redoc`, OpenAPI: `/openapi.json`
