# Architecture + Branching — M1 decision record

Layers: Clients → Nginx/Gateway (M4) → FastAPI (`routers/services/models/schemas`) →
ML layer (M2/M3) → Data (`Postgres 15, Redis 7, Celery, S3`) → External (Stripe-test, SMTP) + Observability.

Module boundaries (doc §3): `user (M1) | catalog+inventory (M2) | order/cart/payment CORE (M2) |
fraud (M2-3) | monitoring (M1 stub→M2) | forecast+recommend (M3) | alerts (M3) | dashboard (M3)`.

M1 structure: `app/{core,db,models,schemas,routers,services}` — routers thin, services hold logic,
schemas version the contract, models own data. `RequireRoles/RequireCapability` is the single RBAC choke point.

Branching: `main` (protected) ← `develop` ← `feat/m1-auth`, `feat/m1-schema`, `feat/m1-docs`.
CI (M4): lint → test (≥80%) → build → push → deploy.
