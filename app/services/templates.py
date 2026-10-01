"""Email templates per event (doc 3.7, M3). Rendered by the Celery worker;
dev/console mode prints them via email_service."""
from string import Template

TEMPLATES = {
    "order_confirmed": ("Order $order_number paid", "Hi $name, payment of $$amount confirmed."),
    "payment_failed": ("Payment failed for $order_number", "Hi $name, please retry — no charge was made."),
    "high_risk_order": ("High-risk order $order_id", "Fraud score $score needs review."),
    "low_stock": ("Low stock: $sku", "Available $available at/below reorder level $reorder_level."),
    "stockout_risk": ("Stock-out risk: $sku", "Forecast covers only $days days. Suggested reorder: $qty."),
    "order_shipped": ("Order $order_number shipped", "Hi $name, your order is on its way."),
    "order_delivered": ("Order $order_number delivered", "Hi $name, enjoy your purchase!"),
    "refund_processed": ("Refund processed for $order_number", "Hi $name, $$amount refunded."),
    "account_locked": ("Account locked", "Hi $name, locked after repeated failed logins. Reset your password."),
    "webhook_failure": ("Payment webhook failure", "Invalid signature or processing error — investigate."),
}


def render(event: str, ctx: dict) -> tuple[str, str]:
    subject, body = TEMPLATES.get(event, (event, str(ctx)))
    safe = {k: v for k, v in ctx.items()}
    return Template(subject).safe_substitute(safe), Template(body).safe_substitute(safe)
