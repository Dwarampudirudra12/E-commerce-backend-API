# Deployment Guide (M4)

## Local / demo (Docker Compose)
```powershell
Copy-Item .env.example .env   # set SECRET_KEY, WEBHOOK_SECRET (32+ chars)
docker compose up --build -d
docker compose exec api alembic upgrade head
docker compose exec api python scripts/seed.py
docker compose exec api python scripts/seed_demand.py
# API http://localhost:8000/docs | metrics /metrics
```
Background jobs: `docker compose --profile jobs up worker beat -d`
Observability: `docker compose --profile monitoring up prometheus grafana -d`
(Grafana http://localhost:3001, Prometheus http://localhost:9090)
Production-like local: `docker compose -f docker-compose.yml -f docker-compose.prod.yml up --build -d`
(gunicorn × 3 workers, no code mounts, `APP_ENV=prod`).

## AWS reference architecture
`Clients -> ALB (ACM TLS cert, HTTPS) -> ECS service (api, 2+ tasks) ->
RDS Postgres 15 (Multi-AZ) + ElastiCache Redis 7; S3 for images;
Secrets Manager for SECRET_KEY / STRIPE keys / DB password.`
`worker`/`beat` run as separate ECS services from the same image.
CI (`.github/workflows/ci.yml`) gates every push: pytest with
`--cov-fail-under=80` against Postgres+Redis services, then `docker build`.

## Environment / secrets (never in git)
`SECRET_KEY`, `DATABASE_URL` (RDS endpoint), `REDIS_URL` (ElastiCache),
`STRIPE_API_KEY`, `STRIPE_WEBHOOK_SECRET`, `WEBHOOK_SECRET`,
`AWS_ACCESS_KEY_ID/SECRET/S3_BUCKET`. `.env` is gitignored; only
`.env.example` (placeholders) is committed. Rotate on any suspected leak.

## Production checklist
- [ ] `APP_ENV=prod`, `DEBUG` off, strong secrets via Secrets Manager
- [ ] RDS automated backups + PITR; ElastiCache replicas per traffic
- [ ] ALB health check `/health/live`; target `/health/ready` for deploys
- [ ] Grafana alerts wired to email/OpsGenie (ApiErrorSpike, HighP95Latency, FraudHoldSpike)
- [ ] `alembic upgrade head` as a deploy step (ECS task or CodeBuild)
- [ ] Nightly `ecom.retrain` via beat; promote only on ROC-AUC improvement
