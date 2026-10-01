"""Payment gateway abstraction — test mode (doc 3.3/M2).

- `mock` (default): in-process intent + HMAC-signed webhooks. Fully testable
  without network or API keys; used by CI and the M2 demo.
- `stripe`: real Stripe test-mode intents (requires stripe package + key).
  Webhook verification implemented manually (timestamped HMAC scheme) so no
  extra dependency is needed in M2.

Both gateways share one webhook contract:
  {event_id, type, gateway_ref, amount}  type: payment.succeeded|payment.failed
"""
import hashlib
import hmac
import time
import uuid

from app.core.config import get_settings


def _mock_sign(body: bytes) -> str:
    return hmac.new(get_settings().WEBHOOK_SECRET.encode(), body, hashlib.sha256).hexdigest()


def verify_mock_signature(body: bytes, signature: str) -> bool:
    return hmac.compare_digest(_mock_sign(body), signature or "")


def verify_stripe_signature(body: bytes, header: str, secret: str) -> bool:
    """Stripe scheme: t=timestamp,v1=hmac(payload 't.body'). 5-min tolerance."""
    try:
        parts = dict(p.split("=", 1) for p in header.split(","))
        ts, v1 = int(parts["t"]), parts["v1"]
        if abs(time.time() - ts) > 300:
            return False
        expect = hmac.new(secret.encode(), f"{ts}.".encode() + body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expect, v1)
    except Exception:
        return False


def create_intent(*, order_id: int, amount: float, currency: str = "USD",
                  idempotency_key: str = "") -> dict:
    """Create a payment intent. Returns {gateway_ref, client_secret, status}."""
    settings = get_settings()
    use_stripe = (settings.PAYMENT_GATEWAY == "stripe"
                  and not settings.STRIPE_API_KEY.startswith("sk_test_placeholder"))
    if use_stripe:
        import stripe  # lazy — only with a real key configured
        stripe.api_key = settings.STRIPE_API_KEY
        pi = stripe.PaymentIntent.create(
            amount=int(round(amount * 100)), currency=currency.lower(),
            metadata={"order_id": order_id}, idempotency_key=idempotency_key or None)
        return {"gateway_ref": pi.id, "client_secret": pi.client_secret, "status": "REQUIRES_ACTION"}
    ref = f"pi_mock_{uuid.uuid4().hex[:16]}"
    return {"gateway_ref": ref, "client_secret": f"{ref}_secret_mock", "status": "PENDING"}


def create_refund(*, gateway_ref: str, amount: float) -> dict:
    settings = get_settings()
    if settings.PAYMENT_GATEWAY == "stripe" and not settings.STRIPE_API_KEY.startswith("sk_test_placeholder"):
        import stripe
        stripe.api_key = settings.STRIPE_API_KEY
        r = stripe.Refund.create(payment_intent=gateway_ref, amount=int(round(amount * 100)))
        return {"gateway_refund_id": r.id, "status": "SUCCEEDED"}
    return {"gateway_refund_id": f"re_mock_{uuid.uuid4().hex[:12]}", "status": "SUCCEEDED"}


def sign_mock_webhook(body: bytes) -> str:
    return _mock_sign(body)
