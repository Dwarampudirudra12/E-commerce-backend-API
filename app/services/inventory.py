"""Stock reservation — the no-oversell guarantee (doc 3.3).

Strategy (works on Postgres AND SQLite):
  Single atomic UPDATE ... WHERE (on_hand - reserved) >= qty.
  The DB executes this atomically, so 50 concurrent buyers of 10 units can
  never reserve more than 10 — no separate check-then-update race.
On Postgres the checkout also takes SELECT ... FOR UPDATE on the rows first
(doc requirement); on SQLite that clause is skipped (unsupported) and the
atomic UPDATE alone still guarantees correctness.
"""
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.models.catalog import Inventory


class InsufficientStock(Exception):
    pass


def _for_update_supported(db: Session) -> bool:
    return db.bind.dialect.name == "postgresql"


def lock_inventory_rows(db: Session, product_ids: list[int]) -> None:
    """Row-level locking for checkout (Postgres). No-op elsewhere."""
    if not product_ids or not _for_update_supported(db):
        return
    db.execute(
        text("SELECT id FROM inventory WHERE product_id = ANY(:ids) FOR UPDATE"),
        {"ids": product_ids},
    )


def reserve_stock(db: Session, *, product_id: int, variant_id: int | None, qty: int) -> Inventory:
    """Atomically reserve qty units. Raises InsufficientStock when short."""
    row = db.execute(
        text(
            "UPDATE inventory SET reserved = reserved + :qty, version = version + 1 "
            "WHERE product_id = :pid "
            "AND (:vid IS NULL AND variant_id IS NULL OR variant_id = :vid) "
            "AND (on_hand - reserved) >= :qty"
        ),
        {"qty": qty, "pid": product_id, "vid": variant_id},
    )
    if row.rowcount != 1:
        raise InsufficientStock(f"product {product_id} short for qty {qty}")
    inv = db.query(Inventory).filter(
        Inventory.product_id == product_id, Inventory.variant_id == variant_id).first()
    return inv


def release_stock(db: Session, *, product_id: int, variant_id: int | None, qty: int) -> None:
    """Release a prior reservation (cancel / failure rollback). Never below 0."""
    db.execute(
        text(
            "UPDATE inventory SET reserved = CASE WHEN reserved - :qty < 0 THEN 0 "
            "ELSE reserved - :qty END, version = version + 1 "
            "WHERE product_id = :pid "
            "AND (:vid IS NULL AND variant_id IS NULL OR variant_id = :vid)"
        ),
        {"qty": qty, "pid": product_id, "vid": variant_id},
    )


def commit_stock(db: Session, *, product_id: int, variant_id: int | None, qty: int) -> None:
    """Move reserved -> sold on payment success: on_hand and reserved both drop."""
    db.execute(
        text(
            "UPDATE inventory SET on_hand = on_hand - :qty, "
            "reserved = CASE WHEN reserved - :qty < 0 THEN 0 ELSE reserved - :qty END, "
            "version = version + 1 "
            "WHERE product_id = :pid "
            "AND (:vid IS NULL AND variant_id IS NULL OR variant_id = :vid)"
        ),
        {"qty": qty, "pid": product_id, "vid": variant_id},
    )
