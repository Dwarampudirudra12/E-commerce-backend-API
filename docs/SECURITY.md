# Security Review (M4, OWASP Top 10)

| Risk | Status |
|---|---|
| Broken access control | RBAC dependency on every route + 403 tests for all 4 roles; customers touch own data only; PAID set by webhook only |
| Cryptographic failures | bcrypt passwords; SHA-256 token hashes; JWT HS256 15m/7d rotation + denylist; TLS terminated at ALB/Nginx in prod |
| Injection | SQLAlchemy ORM everywhere (no string SQL except parameterised `text()` with bound params); Pydantic validation on all inputs |
| Insecure design | Idempotency keys; atomic stock UPDATE (no oversell); state-machine transition map; 423 lockout after 5 fails; 10/60-per-min rate limits on auth/webhook |
| Security misconfiguration | `APP_ENV` gates (prod: no reload/mounts, gunicorn); CORS restricted in prod; `/docs` considered for disablement in prod |
| Vulnerable components | Pinned `requirements.txt`; CI rebuilds image per push |
| Auth failures | Lockout + unlock-by-reset/admin; refresh rotation; OAuth2 + JSON login; token expiry enforced |
| Data/software integrity | Signed webhooks (mock HMAC + Stripe scheme); Alembic-reviewed migrations; CI signs images per SHA |
| Logging/monitoring | JSON request logs with IDs; append-only audit; Prometheus + 3 Grafana alerts |
| SSRF / misc | No user-supplied URLs fetched server-side; S3 uploads keyed server-side |

## Secrets audit (repo, M4)
- `.env` is gitignored and was never committed (only `.env.example` placeholders).
- Verified: `git log --all -p | grep` for `sk_live`, `AKIA`, `SECRET_KEY=.` real values — none found
  (placeholders `change-me` / `sk_test_placeholder` only).
- Stripe runs in test mode; no live keys anywhere.
