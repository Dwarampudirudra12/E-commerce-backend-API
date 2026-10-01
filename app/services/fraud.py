"""Checkout-time fraud scoring (doc 3.4, M3 tuned).

Loads the versioned joblib model at first use (<50ms in-process target);
falls back to a transparent rule-based score when the artefact is missing
so checkout NEVER breaks. Thresholds: <0.30 approve, 0.30-0.70 step-up,
>0.70 hold for Support review.

Explanations: feature ablation against training medians (M3) — the same
top-factor contract SHAP would fill in production.
"""
import logging
import os

import joblib
import numpy as np

from app.ml.features import FEATURES, explain, label_for

log = logging.getLogger(__name__)
_model_bundle = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "fraud_model.joblib")

_FACTOR_MSG = {
    "orders_last_hour": lambda v: f"{int(v) + 1} orders in the last hour",
    "country_mismatch": lambda v: "shipping/billing country mismatch",
    "new_device": lambda v: "new device on this order",
    "failed_payments": lambda v: f"{int(v)} failed payment attempts",
    "discount_ratio": lambda v: f"high discount ({v:.0%})",
    "hour_of_day": lambda v: f"order placed at {int(v)}:00",
    "amount": lambda v: f"high order value (${v:,.0f})",
    "account_age_days": lambda v: f"very new account ({v:.0f} days)",
    "hours_since_last_order": lambda v: "burst after long dormancy",
    "item_count": lambda v: f"large basket ({int(v)} items)",
}


def _bundle():
    global _model_bundle
    if _model_bundle is not None:
        return _model_bundle
    try:
        _model_bundle = joblib.load(MODEL_PATH)
        log.info("fraud model loaded: %s", _model_bundle.get("version"))
    except Exception as e:  # noqa: BLE001 — rule fallback by design
        log.warning("fraud model unavailable (%s), using rule fallback", e)
        _model_bundle = {"model": None}
    return _model_bundle


def _rule_score(f: dict) -> float:
    s = 0.02
    s += min(f.get("orders_last_hour", 0) * 0.15, 0.45)
    s += 0.20 if f.get("country_mismatch") else 0
    s += 0.15 if (f.get("new_device") and f.get("account_age_days", 999) < 7) else 0
    s += min(f.get("failed_payments", 0) * 0.08, 0.24)
    s += 0.10 if f.get("discount_ratio", 0) > 0.5 else 0
    return round(min(max(s, 0.0), 0.99), 4)


def _ablation_factors(model, features: dict, medians: dict, base: float) -> list[str]:
    """Per-feature drop-to-median deltas; top 3 positive contributors."""
    deltas: list[tuple[float, str]] = []
    for k in FEATURES:
        x = np.array([[medians.get(k, 0) if kk == k else float(features.get(kk, 0))
                       for kk in FEATURES]])
        try:
            d = base - float(model.predict_proba(x)[0, 1])
        except Exception:
            continue
        if d > 0.005:
            deltas.append((d, k))
    deltas.sort(reverse=True)
    return [_FACTOR_MSG[k](features.get(k, 0)) for _, k in deltas[:3]]


def score_order(features: dict) -> tuple[float, str, list[str]]:
    """Return (score 0..1, label low|medium|high, top 3 factors)."""
    bundle = _bundle()
    model = bundle.get("model")
    if model is not None:
        try:
            x = np.array([[float(features.get(k, 0)) for k in FEATURES]])
            score = round(float(model.predict_proba(x)[0, 1]), 4)
            factors = _ablation_factors(model, features, bundle.get("medians", {}), score)
            return score, label_for(score), factors or explain(features)
        except Exception:
            pass
    score = _rule_score(features)
    return score, label_for(score), explain(features)


def reset() -> None:
    """Tests only."""
    global _model_bundle
    _model_bundle = None
