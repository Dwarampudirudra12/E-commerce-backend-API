"""Backfill 90 days of demand history per product (M3 forecasting demo).

Weekly seasonality (weekend lift) + mild trend + noise, deterministic seed.
Idempotent: replaces existing rows per product.
Run: docker compose exec api python scripts/seed_demand.py
"""
import os
import sys
from datetime import date, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import numpy as np
from sqlalchemy.orm import Session

from app.db.session import SessionLocal, engine
from app.db.base import Base
import app.models  # noqa: F401
from app.models.catalog import Product
from app.models.observability import DemandHistory


def main(days: int = 90) -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        rng = np.random.default_rng(7)
        today = date.today()
        for p in db.query(Product).all():
            db.query(DemandHistory).filter(DemandHistory.product_id == p.id).delete()
            base = max(1.0, 30.0 / float(p.price))  # cheaper items move faster
            for i in range(days):
                d = today - timedelta(days=days - i)
                weekend = 1.6 if d.weekday() >= 5 else 1.0
                trend = 1.0 + 0.15 * (i / days)
                qty = max(0, int(round(base * weekend * trend + rng.normal(0, base * 0.3))))
                db.add(DemandHistory(product_id=p.id, day=d, qty=qty))
        db.commit()
        print(f"demand seeded: {db.query(DemandHistory).count()} rows")
    finally:
        db.close()


if __name__ == "__main__":
    main()
