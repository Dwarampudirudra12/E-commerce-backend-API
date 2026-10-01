"""Seed a high-stock product for load tests (avoids designed 409s in metrics).

Run: docker compose exec api python scripts/seed_load.py
"""
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy.orm import Session
from app.db.session import SessionLocal, engine
from app.db.base import Base
import app.models  # noqa: F401
from app.models.catalog import Inventory, Product


def main() -> None:
    Base.metadata.create_all(bind=engine)
    db: Session = SessionLocal()
    try:
        p = db.query(Product).filter(Product.sku == "LOAD-1").first()
        if not p:
            p = Product(sku="LOAD-1", name="Load Test Widget", description="M4 load",
                        price=5.0, search_text="load widget load-1")
            db.add(p)
            db.flush()
            db.add(Inventory(product_id=p.id, on_hand=5000, reserved=0, reorder_level=100))
        else:
            inv = db.query(Inventory).filter(Inventory.product_id == p.id,
                                             Inventory.variant_id.is_(None)).first()
            inv.on_hand = max(inv.on_hand, 5000)
        db.commit()
        print("load product ready")
    finally:
        db.close()


if __name__ == "__main__":
    main()
