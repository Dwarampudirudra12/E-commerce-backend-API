"""Baseline fraud trainer (doc 3.4 + M2 groundwork).

- Stratified 70/15/15 split, logistic-regression baseline vs
  HistGradientBoostingClassifier with class weighting.
- Threshold tuned on validation F1; reported on held-out test:
  precision, recall, F1, ROC-AUC, PR-AUC.
- MLflow logging attempted when installed, else skipped (M2 groundwork).
- Artefact: app/ml/artifacts/fraud_model.joblib + fraud_metrics.json.

Run: python -m app.ml.train --n 5000
"""
import argparse
import json
import os

import joblib
import numpy as np
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (average_precision_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split
from sklearn.pipeline import make_pipeline
from sklearn.preprocessing import StandardScaler

from app.ml.features import FEATURES
from app.ml.synthetic import generate

ART_DIR = os.path.join(os.path.dirname(__file__), "artifacts")
MODEL_PATH = os.path.join(ART_DIR, "fraud_model.joblib")
METRICS_PATH = os.path.join(ART_DIR, "fraud_metrics.json")


def _maybe_log_mlflow(params: dict, metrics: dict) -> None:
    try:
        import mlflow
        mlflow.set_experiment("fraud-baseline")
        with mlflow.start_run():
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
    except Exception:
        pass  # MLflow optional in M2


def train(n: int = 5000, seed: int = 42, out_dir: str = ART_DIR) -> dict:
    df = generate(n, seed=seed)
    X, y = df[FEATURES].to_numpy(), df["label"].to_numpy()
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.15, stratify=y, random_state=seed)
    X_tr, X_va, y_tr, y_va = train_test_split(
        X_tr, y_tr, test_size=0.1765, stratify=y_tr, random_state=seed)  # ~15% of total

    candidates = {
        "logreg": make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced")),
        "hgb": HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                              max_leaf_nodes=31, class_weight="balanced",
                                              random_state=seed),
    }
    best = None
    for name, model in candidates.items():
        model.fit(X_tr, y_tr)
        va_proba = model.predict_proba(X_va)[:, 1]
        # Threshold sweep on validation F1.
        ths = np.linspace(0.1, 0.9, 17)
        th = max(ths, key=lambda t: f1_score(y_va, (va_proba >= t).astype(int)))
        te_proba = model.predict_proba(X_te)[:, 1]
        te_pred = (te_proba >= th).astype(int)
        metrics = {
            "model": name, "threshold": round(float(th), 3),
            "precision": round(float(precision_score(y_te, te_pred, zero_division=0)), 4),
            "recall": round(float(recall_score(y_te, te_pred, zero_division=0)), 4),
            "f1": round(float(f1_score(y_te, te_pred, zero_division=0)), 4),
            "roc_auc": round(float(roc_auc_score(y_te, te_proba)), 4),
            "pr_auc": round(float(average_precision_score(y_te, te_proba)), 4),
            "n": n, "test_fraud_rate": round(float(y_te.mean()), 4),
        }
        _maybe_log_mlflow({"model": name, "n": n, "seed": seed}, metrics)
        if best is None or metrics["roc_auc"] > best["metrics"]["roc_auc"]:
            best = {"model": model, "metrics": metrics}

    os.makedirs(out_dir, exist_ok=True)
    joblib.dump({"model": best["model"], "features": FEATURES,
                 "threshold": best["metrics"]["threshold"],
                 "metrics": best["metrics"], "version": "m2-baseline-1"},
                os.path.join(out_dir, "fraud_model.joblib"))
    with open(os.path.join(out_dir, "fraud_metrics.json"), "w") as f:
        json.dump(best["metrics"], f, indent=2)
    return best["metrics"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    m = train(ap.parse_args().n)
    print(json.dumps(m, indent=2))
