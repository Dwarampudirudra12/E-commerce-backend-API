"""Proactive alert rules (doc 3.7, M3). Each rule writes Notification rows
(consumed by the inbox API, email worker and dashboard alerts panel)."""
from sqlalchemy.orm import Session

from app.models.catalog import Inventory, Product
from app.models.observability import Notification


def check_low_stock(db: Session, product_id: int) -> bool:
    """Fire once per product per day when available <= reorder level."""
    inv = db.query(Inventory).filter(Inventory.product_id == product_id,
                                     Inventory.variant_id.is_(None)).first()
    p = db.query(Product).filter(Product.id == product_id).first()
    if not inv or not p or (inv.on_hand - inv.reserved) > inv.reorder_level:
        return False
    recent = db.query(Notification).filter(Notification.type == "low_stock").all()
    if any((n.payload or {}).get("product_id") == product_id for n in recent[-50:]):
        return False  # crude 1-per-day-ish dedupe without extra queries
    db.add(Notification(user_id=p.seller_id, type="low_stock", channel="in_app",
                        status="SENT",
                        payload={"product_id": p.id, "sku": p.sku,
                                 "available": inv.on_hand - inv.reserved,
                                 "reorder_level": inv.reorder_level}))
    return True


def _error_rate() -> tuple[float, float]:
    """(5xx count, total count) from the process Prometheus registry."""
    from prometheus_client import REGISTRY
    err, tot = 0.0, 0.0
    for metric in REGISTRY.collect():
        for s in metric.samples:
            if s.name == "http_requests_total":
                tot += s.value
                if s.labels.get("status", "").startswith("5"):
                    err += s.value
    return err, tot


def check_api_error_spike(db: Session, *, window: str = "5m", threshold: float = 0.02) -> bool:
    """5xx rate above threshold -> Critical admin alert (doc 3.7)."""
    err, tot = _error_rate()
    if tot >= 20 and err / tot > threshold:
        db.add(Notification(user_id=None, type="api_error_spike", channel="in_app",
                            status="SENT",
                            payload={"error_rate": round(err / tot, 4), "window": window}))
        db.commit()
        return True
    return False
