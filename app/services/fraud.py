"""Checkout-time fraud scoring (doc 3.4).

Loads the versioned joblib model at first use (<50ms in-process target);
falls back to a transparent rule-based score when the artefact is missing
so checkout NEVER breaks. Thresholds: <0.30 approve, 0.30-0.70 step-up,
>0.70 hold for Support review.
"""
import logging
import os

import joblib
import numpy as np

from app.ml.features import APPROVE_BELOW, FEATURES, HOLD_ABOVE, explain, label_for

log = logging.getLogger(__name__)
_model_bundle = None
MODEL_PATH = os.path.join(os.path.dirname(__file__), "ml", "artifacts", "fraud_model.joblib")


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


def score_order(features: dict) -> tuple[float, str, list[str]]:
    """Return (score 0..1, label low|medium|high, top 3 factors)."""
    bundle = _bundle()
    model = bundle.get("model")
    if model is not None:
        try:
            x = np.array([[float(features.get(k, 0)) for k in FEATURES]])
            score = round(float(model.predict_proba(x)[0, 1]), 4)
        except Exception:
            score = _rule_score(features)
    else:
        score = _rule_score(features)
    return score, label_for(score), explain(features)


def reset() -> None:
    """Tests only."""
    global _model_bundle
    _model_bundle = None
