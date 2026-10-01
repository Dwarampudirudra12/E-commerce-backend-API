"""Fraud feature contract (doc 3.4) — single source of truth shared by the
synthetic generator, the trainer, and checkout-time scoring. Order matters."""
from datetime import datetime

FEATURES = [
    "amount",                 # order total
    "item_count",             # total units
    "discount_ratio",         # discount / subtotal (0..1)
    "account_age_days",       # user age
    "hours_since_last_order", # recency (large = dormant)
    "orders_last_hour",       # velocity
    "failed_payments",        # failed payment attempts on account
    "country_mismatch",       # shipping vs billing country (0/1)
    "new_device",             # unseen device flag (0/1)
    "hour_of_day",            # 0..23
]

APPROVE_BELOW = 0.30
HOLD_ABOVE = 0.70


def label_for(score: float) -> str:
    if score < APPROVE_BELOW:
        return "low"
    if score > HOLD_ABOVE:
        return "high"
    return "medium"


def explain(features: dict) -> list[str]:
    """Top contributing factors in plain language (SHAP arrives in M3)."""
    reasons: list[str] = []
    v = features.get("orders_last_hour", 0)
    if v >= 3:
        reasons.append(f"{int(v) + 1} orders in the last hour")
    if features.get("country_mismatch"):
        reasons.append("shipping/billing country mismatch")
    if features.get("new_device") and features.get("account_age_days", 999) < 7:
        reasons.append("new device on a new account")
    if features.get("failed_payments", 0) >= 2:
        reasons.append(f"{int(features['failed_payments'])} failed payment attempts")
    if features.get("discount_ratio", 0) > 0.5:
        reasons.append("unusually high discount")
    h = features.get("hour_of_day", 12)
    if h < 5 or h >= 23:
        reasons.append(f"order placed at {int(h)}:00")
    if features.get("amount", 0) > 500 and features.get("account_age_days", 999) < 30:
        reasons.append("high value on a young account")
    return reasons[:3]


def now_hour() -> int:
    return datetime.now().hour
