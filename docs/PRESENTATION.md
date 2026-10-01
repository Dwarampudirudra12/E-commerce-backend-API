# Final Demo Script (M4, ~8 min)

1. **Architecture (1 min)** — `docs/ARCHITECTURE.md`: gateway → FastAPI →
   ML layer → Postgres/Redis/Celery; `/docs` open live.
2. **Browse-to-pay (2 min)** — Swagger: register customer, search catalog,
   cart add, `POST /orders` with Idempotency-Key → totals math on screen;
   show retried key returns the SAME order.
3. **Payment (1 min)** — signed webhook → PAID; show stock committed,
   audit rows, confirmation notification.
4. **Fraud (1 min)** — crafted risky order → ON_HOLD → review queue with
   factors → approve → intent created. Metrics: ROC-AUC 0.96.
5. **Forecast + dashboard (1.5 min)** — React dashboard: KPIs, revenue trend,
   reorder table; forecast endpoint MAPE 19.45%.
6. **Ops (1 min)** — `/metrics`, Grafana alerts, load-test numbers
   (p95 checkout 1.4 s, 0.05% errors @200 users), coverage 84%.
7. **Close (30 s)** — milestones on GitHub (`main`/`develop`/`feat/*`),
   CI green, AWS path in `docs/DEPLOYMENT.md`.
