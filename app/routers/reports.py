"""Analytics endpoints (doc 3.8, M3): KPIs, trends, top products, fraud
distribution, CSV export. Admin sees all; sellers see own products only."""
import csv
import io
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import PlainTextResponse
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import RequireAdmin, RequireSeller
from app.db.session import get_db
from app.models.cart_order import Order, OrderItem
from app.models.catalog import Inventory, Product
from app.models.observability import MlPrediction
from app.models.payment import Refund
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


def _scoped_orders(db: Session, user: User):
    q = db.query(Order)
    if user.role == "SELLER":
        my_pids = [p.id for p in db.query(Product).filter(Product.seller_id == user.id).all()]
        oids = [oi.order_id for oi in db.query(OrderItem).filter(
            OrderItem.product_id.in_(my_pids)).all()] if my_pids else []
        q = q.filter(Order.id.in_(oids)) if oids else q.filter(Order.id == -1)
    return q


def _kpis(orders: list[Order], db: Session, user: User) -> dict:
    live = [o for o in orders if o.status not in ("CANCELLED",)]
    revenue = round(sum(float(o.total) for o in live if o.status != "REFUNDED"), 2)
    refunds = db.query(Refund).count() if user.role == "ADMIN" else 0
    held = sum(1 for o in live if o.status == "ON_HOLD")
    low_stock = 0
    products = db.query(Product)
    if user.role == "SELLER":
        products = products.filter(Product.seller_id == user.id)
    for p in products.all():
        inv = db.query(Inventory).filter(Inventory.product_id == p.id,
                                         Inventory.variant_id.is_(None)).first()
        if inv and (inv.on_hand - inv.reserved) <= inv.reorder_level:
            low_stock += 1
    return {"revenue": revenue, "orders": len(live),
            "average_order_value": round(revenue / len(live), 2) if live else 0.0,
            "refund_rate": round(refunds / max(len(live), 1), 4),
            "fraud_held": held, "low_stock_count": low_stock}


@router.get("/sales/summary")
def sales_summary(from_date: str | None = Query(None), to_date: str | None = Query(None),
                  user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    if user.role not in ("ADMIN", "SELLER"):
        raise HTTPException(403, "Admins and sellers only")
    q = _scoped_orders(db, user)
    if from_date:
        q = q.filter(Order.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.filter(Order.created_at <= datetime.fromisoformat(to_date))
    orders = q.all()
    out = _kpis(orders, db, user)
    by_status: dict[str, int] = {}
    for o in orders:
        by_status[o.status] = by_status.get(o.status, 0) + 1
    out["by_status"] = by_status
    return out


@router.get("/revenue-trend")
def revenue_trend(days: int = Query(30, ge=1, le=365),
                  user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    if user.role not in ("ADMIN", "SELLER"):
        raise HTTPException(403, "Admins and sellers only")
    since = datetime.now() - timedelta(days=days)
    orders = _scoped_orders(db, user).filter(Order.created_at >= since,
                                            Order.status.notin_(["CANCELLED", "REFUNDED"])).all()
    buckets: dict[str, float] = {}
    for o in orders:
        day = o.created_at.date().isoformat() if o.created_at else "unknown"
        buckets[day] = round(buckets.get(day, 0) + float(o.total), 2)
    return {"points": [{"day": d, "revenue": buckets[d]} for d in sorted(buckets)]}


@router.get("/top-products")
def top_products(limit: int = Query(10, ge=1, le=50),
                 user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    if user.role not in ("ADMIN", "SELLER"):
        raise HTTPException(403, "Admins and sellers only")
    q = db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("units"),
                 func.sum(OrderItem.subtotal).label("revenue"))
    if user.role == "SELLER":
        q = q.join(Product, Product.id == OrderItem.product_id
                   ).filter(Product.seller_id == user.id)
    rows = q.group_by(OrderItem.product_id
                      ).order_by(func.sum(OrderItem.quantity).desc()).limit(limit).all()
    items = []
    for pid, units, revenue in rows:
        p = db.query(Product).filter(Product.id == pid).first()
        items.append({"product_id": pid, "sku": p.sku if p else None,
                      "name": p.name if p else None, "units": int(units),
                      "revenue": float(revenue)})
    return {"items": items}


@router.get("/fraud-distribution")
def fraud_distribution(admin: User = Depends(RequireAdmin), db: Session = Depends(get_db)):
    buckets = {"low": 0, "medium": 0, "high": 0}
    for (label,) in db.query(MlPrediction.label).filter(MlPrediction.model_name == "fraud").all():
        buckets[label or "medium"] = buckets.get(label or "medium", 0) + 1
    return buckets


@router.get("/export.csv", response_class=PlainTextResponse)
def export_csv(kind: str = Query("orders", pattern="^(orders|products)$"),
               user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    if user.role not in ("ADMIN", "SELLER"):
        raise HTTPException(403, "Admins and sellers only")
    buf = io.StringIO()
    if kind == "orders":
        w = csv.writer(buf)
        w.writerow(["id", "order_number", "status", "total", "created_at"])
        for o in _scoped_orders(db, user).order_by(Order.id).limit(5000).all():
            w.writerow([o.id, o.order_number, o.status, float(o.total), o.created_at])
    else:
        w = csv.writer(buf)
        w.writerow(["id", "sku", "name", "price", "is_active"])
        q = db.query(Product)
        if user.role == "SELLER":
            q = q.filter(Product.seller_id == user.id)
        for p in q.order_by(Product.id).limit(5000).all():
            w.writerow([p.id, p.sku, p.name, float(p.price), p.is_active])
    return buf.getvalue()
