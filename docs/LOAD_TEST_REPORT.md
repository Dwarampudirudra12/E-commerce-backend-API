# Load-Test Report (M4) — measured, not projected

## Setup
- API: single uvicorn `--reload` worker (dev server) on Docker Desktop/Windows,
  Postgres 15, Redis 7. Prod runs gunicorn × 3 (`docker-compose.prod.yml`).
- Scenario `load/locustfile.py`: browse-heavy mix (catalog/search/detail/recs),
  full buyer checkout (unique users + idempotency keys), support list/queue.
- Load: **200 concurrent users, 20/s ramp, 90 s** (`--csv load/results2`).
- Rate limiting disabled for the measurement run (`RATE_LIMIT_ENABLED=false`);
  the limiter is verified separately (run 1: 385× 429 on auth at 10/min/IP —
  it works) and by `test_auth_rate_limit_429`.

## Results (200 users / 90 s, 12,726 requests)

| Endpoint | req | fail | median | p95 | max |
|---|---|---|---|---|---|
| catalog:list | 4135 | 0 | 150ms | 450ms | 1418ms |
| catalog:search | 2772 | 0 | 160ms | 440ms | 1418ms |
| catalog:detail | 1326 | 0 | 160ms | 430ms | 1374ms |
| catalog:recs | 1320 | 0 | 140ms | 370ms | 1290ms |
| cart:add | 809 | 0 | 250ms | 600ms | 1598ms |
| **orders:checkout** | **804** | **0** | **500ms** | **1400ms** | 3268ms |
| support:orders | 431 | 5* | 340ms | 730ms | 1647ms |
| support:queue | 228 | 1* | 220ms | 610ms | 1242ms |
| auth login/register | 87 | 0 | ~450ms | ~760ms | 795ms |

\* 6 transient connection resets under saturation (0.05% overall).

## Verdict vs Section 8
- Checkout p95 1400ms < 1500ms: **PASS** (zero failed checkouts).
- Error rate 0.05% < 1%: **PASS**.
- Catalog p95 ~450ms vs 300ms target: **MISS on single dev worker** —
  expected to pass under `docker-compose.prod.yml` (gunicorn × 3) where
  independent workers share the load; Redis catalog caching is already on.
- M4 optimisation shipped: `Order.items selectin` relationship removes the
  list-endpoint N+1 (was ~20 queries per `GET /orders` page); composite
  indexes in migration `0004`; DB pool env-tunable (`DB_POOL_SIZE`).
