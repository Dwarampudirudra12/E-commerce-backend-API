"""Synthetic order generator (doc 3.4: real store data unavailable).

Fraud pattern injected (~5% prior): new account + high velocity + country
mismatch + odd hour + large amount. Everything else is genuine noise.
Run: python -m app.ml.synthetic --n 5000 --out app/ml/data/synthetic_orders.csv
"""
import argparse
import os

import numpy as np
import pandas as pd

from app.ml.features import FEATURES


def generate(n: int = 5000, fraud_prior: float = 0.05, seed: int = 42) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    fraud = rng.random(n) < fraud_prior

    # Overlapping distributions + 1.5% label noise: realistic, non-trivial signal.
    amount = np.where(fraud,
                      rng.lognormal(4.6, 1.0, n),
                      rng.lognormal(3.5, 0.9, n)).round(2)
    item_count = np.where(fraud, rng.integers(1, 10, n), rng.integers(1, 6, n))
    discount_ratio = np.where(fraud, rng.beta(3, 3, n) * 0.7, rng.beta(2, 8, n) * 0.35).round(3)
    account_age = np.where(fraud, rng.exponential(15, n), 30 + rng.exponential(300, n)).round(1)
    hours_since = np.where(fraud, rng.exponential(10, n), rng.exponential(200, n)).round(1)
    velocity = np.where(fraud, rng.integers(1, 6, n),
                        rng.choice([0, 0, 0, 0, 0, 1, 1, 2, 3], n))
    failed = np.where(fraud, rng.integers(0, 4, n),
                      rng.choice([0, 0, 0, 0, 0, 0, 1, 2], n))
    mismatch = np.where(fraud, rng.random(n) < 0.55, rng.random(n) < 0.08).astype(int)
    new_device = np.where(fraud, rng.random(n) < 0.65, rng.random(n) < 0.25).astype(int)
    night = rng.random(n) < 0.10
    hour = np.where(fraud, rng.choice([0, 1, 2, 3, 4, 22, 23], n),
                    np.where(night, rng.integers(0, 6, n), rng.integers(6, 24, n)))
    labels = fraud.astype(int)
    flip = rng.random(n) < 0.015  # label noise
    labels = np.where(flip, 1 - labels, labels)

    df = pd.DataFrame({
        "amount": amount, "item_count": item_count, "discount_ratio": discount_ratio,
        "account_age_days": account_age, "hours_since_last_order": hours_since,
        "orders_last_hour": velocity, "failed_payments": failed,
        "country_mismatch": mismatch, "new_device": new_device,
        "hour_of_day": hour, "label": labels,
    })
    return df[FEATURES + ["label"]]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=5000)
    ap.add_argument("--out", default="app/ml/data/synthetic_orders.csv")
    a = ap.parse_args()
    df = generate(a.n)
    os.makedirs(os.path.dirname(a.out), exist_ok=True)
    df.to_csv(a.out, index=False)
    print(f"wrote {a.out}: {len(df)} rows, fraud_rate={df.label.mean():.3f}")
