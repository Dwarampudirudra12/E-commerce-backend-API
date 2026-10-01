# User Manual (M4) — per role quick paths

Base URL autodoc: `/docs` (Swagger, try every endpoint). All API calls send
`Authorization: Bearer <access_token>` except guest catalog browsing.

## Customer
1. `POST /auth/register` (CUSTOMER) -> verify email (`POST /auth/verify-email`).
2. `POST /auth/login` -> tokens (access 15 min; `POST /auth/refresh` to renew).
3. Browse `GET /products`, `GET /products/search?q=...&sort=price`.
4. `POST /cart/items` -> `GET /cart` -> `POST /orders` **with `Idempotency-Key`
   header** (safe to retry on network errors — same key returns the same order).
5. Pay: test-mode intent is created automatically; the gateway calls
   `POST /payments/webhook` (signed). Track `GET /orders/{id}` to DELIVERED.
6. Cancel pre-shipment: `PATCH /orders/{id}/status` → `CANCELLED`.
7. Personal picks: `GET /users/me/recommendations`; inbox: `GET /notifications/me`.

## Seller
Register with `"role": "SELLER"`. Create products (`POST /products`), variants,
images (`POST /products/{id}/images`); set stock (`PATCH .../inventory` with the
current `version`). Watch `GET /forecasts/reorder-suggestions` and the
dashboard Products tab. Fulfil: `PATCH /orders/{id}/status` → PACKED → SHIPPED.

## Support Agent (created by admin)
Review `GET /orders/review/queue` (risk factors included); approve
(→ `PENDING_PAYMENT` + intent) or reject (→ `CANCELLED`). Refunds
(`POST /payments/{id}/refund`) up to $100; larger need an admin.

## Administrator
Manage users/roles (`GET /users`, `PATCH /users/{id}/role`, unlock),
categories, analytics (`/reports/*`, CSV export), audit via DB,
alert thresholds in Grafana, model retraining (`python -m app.ml.train --n 30000 --tuned`).

Demo accounts (seeded): `customer@ / seller@ / support@ / admin@example.com`,
password `Password123!`.
