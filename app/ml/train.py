"""Fraud trainer: M2 baseline + M3 tuned search (doc 3.4).

- M2: logreg baseline vs default HGB.
- M3 (--tuned): small HGB grid + threshold chosen on validation for
  precision >= 0.70 with max recall (Section 8: recall >= 80% @ precision >= 70%).
- Stratified 70/15/15, MLflow optional, joblib artefact + metrics JSON.

Run: python -m app.ml.train --n 15000 --tuned
"""
import argparse
import itertools
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

HGB_GRID = {
    "learning_rate": [0.03, 0.06],
    "max_leaf_nodes": [15, 31],
    "min_samples_leaf": [10, 20, 50],
}


def _maybe_log_mlflow(params: dict, metrics: dict) -> None:
    try:
        import mlflow
        mlflow.set_experiment("fraud")
        with mlflow.start_run():
            mlflow.log_params(params)
            mlflow.log_metrics(metrics)
    except Exception:
        pass  # MLflow optional


def _split(X, y, seed):
    X_tr, X_te, y_tr, y_te = train_test_split(X, y, test_size=0.15, stratify=y, random_state=seed)
    X_tr, X_va, y_tr, y_va = train_test_split(
        X_tr, y_tr, test_size=0.1765, stratify=y_tr, random_state=seed)
    return (X_tr, y_tr), (X_va, y_va), (X_te, y_te)


def _pick_threshold(y_va, proba_va) -> tuple[float, bool]:
    """Precision >= 0.70 with max recall; flag says whether it was feasible."""
    ths = np.linspace(0.05, 0.95, 37)
    feasible = [(t, recall_score(y_va, (proba_va >= t).astype(int), zero_division=0))
                for t in ths
                if precision_score(y_va, (proba_va >= t).astype(int), zero_division=0) >= 0.70]
    if feasible:
        return round(float(max(feasible, key=lambda x: x[1])[0]), 3), True
    best = max(ths, key=lambda t: f1_score(y_va, (proba_va >= t).astype(int), zero_division=0))
    return round(float(best), 3), False


def _evaluate(model, X_te, y_te, threshold) -> dict:
    proba = model.predict_proba(X_te)[:, 1]
    pred = (proba >= threshold).astype(int)
    return {
        "threshold": threshold,
        "precision": round(float(precision_score(y_te, pred, zero_division=0)), 4),
        "recall": round(float(recall_score(y_te, pred, zero_division=0)), 4),
        "f1": round(float(f1_score(y_te, pred, zero_division=0)), 4),
        "roc_auc": round(float(roc_auc_score(y_te, proba)), 4),
        "pr_auc": round(float(average_precision_score(y_te, proba)), 4),
    }


def train(n: int = 5000, seed: int = 42, out_dir: str = ART_DIR,
          tuned: bool = False) -> dict:
    df = generate(n, seed=seed)
    X, y = df[FEATURES].to_numpy(), df["label"].to_numpy()
    (X_tr, y_tr), (X_va, y_va), (X_te, y_te) = _split(X, y, seed)

    candidates: list[tuple[str, dict, object]] = [
        ("logreg", {"model": "logreg"},
         make_pipeline(StandardScaler(), LogisticRegression(max_iter=2000, class_weight="balanced"))),
    ]
    if tuned:
        for lr, leaves, min_leaf in itertools.product(
                HGB_GRID["learning_rate"], HGB_GRID["max_leaf_nodes"], HGB_GRID["min_samples_leaf"]):
            candidates.append(
                (f"hgb_lr{lr}_leaf{leaves}_min{min_leaf}",
                 {"model": "hgb", "lr": lr, "leaves": leaves, "min_leaf": min_leaf},
                 HistGradientBoostingClassifier(max_iter=400, learning_rate=lr,
                                                max_leaf_nodes=leaves, min_samples_leaf=min_leaf,
                                                l2_regularization=1.0, class_weight="balanced",
                                                random_state=seed)))
    else:
        candidates.append(
            ("hgb", {"model": "hgb"},
             HistGradientBoostingClassifier(max_iter=300, learning_rate=0.06,
                                            max_leaf_nodes=31, class_weight="balanced",
                                            random_state=seed)))

    best = None
    for name, params, model in candidates:
        model.fit(X_tr, y_tr)
        th, feasible = _pick_threshold(y_va, model.predict_proba(X_va)[:, 1])
        m = _evaluate(model, X_te, y_te, th)
        m.update({"model": name, "n": n, "test_fraud_rate": round(float(y_te.mean()), 4),
                  "precision_constrained": feasible})
        _maybe_log_mlflow({**params, "n": n, "seed": seed, "threshold": th}, m)
        if best is None or m["roc_auc"] > best["metrics"]["roc_auc"]:
            best = {"model": model, "metrics": m}

    os.makedirs(out_dir, exist_ok=True)
    version = "m3-tuned-1" if tuned else "m2-baseline-1"
    joblib.dump({"model": best["model"], "features": FEATURES,
                 "threshold": best["metrics"]["threshold"],
                 "medians": {k: float(v) for k, v in df[FEATURES].median().items()},
                 "metrics": best["metrics"], "version": version},
                os.path.join(out_dir, "fraud_model.joblib"))
    with open(os.path.join(out_dir, "fraud_metrics.json"), "w") as f:
        json.dump(best["metrics"], f, indent=2)
    return best["metrics"]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--tuned", action="store_true")
    args = ap.parse_args()
    print(json.dumps(train(args.n, tuned=args.tuned), indent=2))
