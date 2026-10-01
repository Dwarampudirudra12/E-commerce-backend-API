"""Fraud baseline: generator contract, rule fallback, training smoke test."""
import app.services.fraud as fraud_svc
from app.ml.features import FEATURES


def test_generator_shape_and_prior():
    from app.ml.synthetic import generate
    df = generate(2000, seed=7)
    assert list(df.columns) == FEATURES + ["label"]
    assert 0.02 < df["label"].mean() < 0.10  # ~5% prior


def test_rule_fallback_low_risk():
    fraud_svc._model_bundle = {"model": None}
    score, label, _ = fraud_svc.score_order(
        {"amount": 40, "item_count": 2, "discount_ratio": 0.0,
         "account_age_days": 400, "hours_since_last_order": 100,
         "orders_last_hour": 0, "failed_payments": 0,
         "country_mismatch": 0, "new_device": 0, "hour_of_day": 14})
    assert label == "low" and score < 0.30
    fraud_svc.reset()


def test_rule_fallback_high_risk_with_factors():
    fraud_svc._model_bundle = {"model": None}
    score, label, factors = fraud_svc.score_order(
        {"amount": 900, "item_count": 9, "discount_ratio": 0.6,
         "account_age_days": 0.2, "hours_since_last_order": 0.5,
         "orders_last_hour": 4, "failed_payments": 3,
         "country_mismatch": 1, "new_device": 1, "hour_of_day": 2})
    assert label == "high" and score > 0.70
    assert len(factors) >= 2
    fraud_svc.reset()


def test_train_small_reports_roc_auc(tmp_path):
    from app.ml.train import train
    m = train(n=800, seed=11, out_dir=str(tmp_path))
    assert m["roc_auc"] >= 0.80, m
    assert {"precision", "recall", "f1", "pr_auc", "threshold"} <= set(m)
