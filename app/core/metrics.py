"""Prometheus metrics (doc 3.5). Real counters wired in M2; /metrics serves exposition."""
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest

HTTP_REQUESTS = Counter("http_requests_total", "HTTP requests", ["method", "route", "status"])
HTTP_LATENCY = Histogram("http_request_duration_seconds", "HTTP latency", ["route"])
ORDERS_CREATED = Counter("orders_created_total", "Orders created", ["outcome"])
# outcome: created | held_fraud | conflict | idempotent_hit
PAYMENT_WEBHOOKS = Counter("payment_webhooks_total", "Payment webhooks", ["result"])
# result: paid | failed | duplicate | rejected
FRAUD_SCORED = Counter("fraud_scored_total", "Fraud scorings", ["label"])


def exposition() -> tuple[bytes, str]:
    return generate_latest(), CONTENT_TYPE_LATEST
