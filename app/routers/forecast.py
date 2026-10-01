"""Forecast + reorder endpoints (doc 3.6, M3). Seller sees own products, admin all."""
from datetime import date, timedelta

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core import cache
from app.core.deps import RequireAdmin, RequireSeller
from app.db.session import get_db
from app.ml.forecast import days_until_stockout, forecast, holdout_mape, reorder_qty
from app.models.catalog import Inventory, Product
from app.models.observability import DemandHistory, MlPrediction, Notification
from app.models.user import User

router = APIRouter(prefix="/forecasts", tags=["forecasts"])
HORIZON = 14


def _history(db: Session, product_id: int) -> list[tuple[date, int]]:
    rows = db.query(DemandHistory).filter(DemandHistory.product_id == product_id
                                          ).order_by(DemandHistory.day).all()
    return [(r.day, r.qty) for r in rows]


def _scope_products(db: Session, user: User) -> list[Product]:
    q = db.query(Product).filter(Product.is_active == True)  # noqa: E712
    if user.role == "SELLER":
        q = q.filter(Product.seller_id == user.id)
    return q.all()


@router.get("/products/{product_id}")
def product_forecast(product_id: int, horizon: int = Query(14, ge=1, le=30),
                     user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    if user.role == "SELLER" and p.seller_id != user.id:
        raise HTTPException(403, "Only the owning seller")
    key = cache.cache_key("forecast", str(product_id), str(horizon))
    if (hit := cache.cache_get(key)) is not None:
        return hit
    hist = _history(db, product_id)
    preds, model = forecast(hist, horizon)
    mape, _ = holdout_mape(hist)
    today = date.today()
    out = {"product_id": product_id, "model": model, "history_days": len(hist),
           "holdout_mape_pct": mape,
           "forecast": [{"day": (today + timedelta(days=i + 1)).isoformat(), "qty": q}
                        for i, q in enumerate(preds)]}
    db.add(MlPrediction(model_name="forecast", model_version="m3-1", entity_type="product",
                        entity_id=str(product_id), score=mape, label=model,
                        top_factors={"horizon": horizon}))
    db.commit()
    cache.cache_set(key, out, ttl=3600)
    return out


@router.get("/reorder-suggestions")
def reorder_suggestions(user: User = Depends(RequireSeller), db: Session = Depends(get_db)):
    suggestions = []
    for p in _scope_products(db, user):
        hist = _history(db, p.id)
        preds, model = forecast(hist, HORIZON)
        inv = db.query(Inventory).filter(Inventory.product_id == p.id,
                                         Inventory.variant_id.is_(None)).first()
        on_hand = inv.on_hand if inv else 0
        reserved = inv.reserved if inv else 0
        available = on_hand - reserved
        dus = days_until_stockout(available, preds)
        qty = reorder_qty(preds, on_hand=on_hand)
        at_risk = dus is not None and dus <= 7
        if at_risk:
            db.add(Notification(user_id=p.seller_id, type="stockout_risk", channel="in_app",
                                status="SENT",
                                payload={"product_id": p.id, "sku": p.sku,
                                         "days_until_stockout": dus, "reorder_qty": qty}))
        suggestions.append({"product_id": p.id, "sku": p.sku, "model": model,
                            "on_hand": on_hand, "available": available,
                            "forecast_14d": round(sum(preds), 1),
                            "days_until_stockout": dus, "reorder_qty": qty,
                            "at_risk": at_risk})
    db.commit()
    suggestions.sort(key=lambda s: (not s["at_risk"], s["days_until_stockout"] or 999))
    return {"items": suggestions}


# Admin-only alias (same data, explicit role for the M3 dashboard).
@router.get("/admin/reorder-suggestions")
def admin_reorder_suggestions(admin: User = Depends(RequireAdmin),
                              db: Session = Depends(get_db)):
    return reorder_suggestions(user=admin, db=db)
