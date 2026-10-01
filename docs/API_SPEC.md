# API Specification — M1 + M2 (implemented)

Base: `/api/v1`. Errors: `{detail, code, request_id?}`. Auth: `Bearer <access-token>`.

## Auth (`/auth`)
| Method | Path | Auth | Notes |
|---|---|---|---|
| POST | `/auth/register` | — | CUSTOMER/SELLER only; SUPPORT/ADMIN → 403 |
| POST | `/auth/login` | — | JSON `{email,password}`; 423 when locked |
| POST | `/auth/token` | — | OAuth2 form (Swagger Authorize) |
| POST | `/auth/refresh` | — | Rotates refresh token |
| POST | `/auth/logout` | Bearer | Revokes supplied refresh token |
| POST | `/auth/verify-email` | — | `{token}` 24h |
| POST | `/auth/forgot-password` | — | Always 200 (no enumeration) |
| POST | `/auth/reset-password` | — | `{token,new_password}`; unlocks account |

## Users (`/users`)
| Method | Path | Roles |
|---|---|---|
| GET/PATCH | `/users/me`, `/users/me/addresses` | any authenticated |
| GET | `/users` | ADMIN |
| PATCH | `/users/{id}/role` | ADMIN |
| POST | `/users/{id}/unlock` | ADMIN |

## System
| Method | Path | Notes |
|---|---|---|
| GET | `/health/live`, `/health/ready` | readiness checks DB |
| GET | `/docs`, `/redoc`, `/openapi.json` | OpenAPI (M1 criterion #4) |

## M2: catalog, cart, orders, payments, reports (implemented)

| Method | Path | Roles | Notes |
|---|---|---|---|
| POST | `/categories` | ADMIN | create category |
| GET | `/categories` | — | guest OK |
| POST | `/products` | SELLER own / ADMIN | creates zero-stock inventory row |
| GET | `/products`, `/products/search` | — | guest OK; filters, sort, pagination; Redis-cached |
| GET/PATCH | `/products/{id}`, `/products/{id}/variants` | read — / write SELLER own |  |
| GET/PATCH | `/products/{id}/inventory` | SELLER own / ADMIN | optimistic `version`, 409 on stale |
| POST | `/products/{id}/images` | SELLER own / ADMIN | S3 when configured else `/uploads` |
| GET/POST/PATCH/DELETE | `/cart`, `/cart/items` | CUSTOMER | persistent cart |
| POST | `/orders` | CUSTOMER | **requires `Idempotency-Key`**; 409 when short |
| GET | `/orders`, `/orders/{id}` | CUSTOMER own / SELLER own-products / SUPPORT+ADMIN all | |
| PATCH | `/orders/{id}/status` | role-gated state machine; PAID webhook-only | |
| GET | `/payments/by-order/{order_id}` | owner + staff | intent status |
| POST | `/payments/webhook` | signed (X-Signature / Stripe-Signature) | idempotent via event_id |
| POST | `/payments/{id}/refund` | SUPPORT ≤ $100 / ADMIN unlimited | restocks on full refund |
| GET | `/reports/sales/summary` | ADMIN | revenue, orders, AOV, by-status |

Checkout math: 8% tax, $4 flat shipping (free ≥ $50), discount-code %.
Fraud: score recorded per order (`ml_predictions`); >0.70 → ON_HOLD.

## RBAC matrix (doc p3)
| Capability | Guest | Customer | Seller | Support | Admin |
|---|---|---|---|---|---|
| Browse catalog | ✓ | ✓ | ✓ | ✓ | ✓ |
| Manage cart/order | – | ✓ | – | – | – |
| Create/edit products | – | – | ✓ own | – | ✓ |
| Update inventory | – | – | ✓ own | – | ✓ |
| View all orders / fraud review | – | – | – | ✓ | ✓ |
| Refunds | – | – | – | ✓ limit | ✓ |
| Manage users / audit | – | – | – | – | ✓ |
