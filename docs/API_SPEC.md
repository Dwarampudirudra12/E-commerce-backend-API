# API Specification — M1 (implemented) + M2 preview

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

## M2 preview (not yet)
`POST /api/v1/products`, `GET /api/v1/products/search`, `POST /api/v1/cart/items`,
`POST /api/v1/orders` (Idempotency-Key), `POST /api/v1/payments/webhook`.

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
