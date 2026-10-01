"""Recommendation endpoints (doc 3.6, M3): bought-together, also-viewed,
personalised. Popular-in-category fallback for cold start. Cached 5 min."""
import jwt
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core import cache
from app.core.config import get_settings
from app.core.deps import get_current_user
from app.db.session import get_db
from app.ml.recommend import personal_for, similar_items
from app.models.cart_order import Order, OrderItem
from app.models.catalog import Product
from app.models.observability import ProductView
from app.models.user import User

router = APIRouter(tags=["recommendations"])
_opt_bearer = HTTPBearer(auto_error=False)


def _optional_user(creds: HTTPAuthorizationCredentials | None = Depends(_opt_bearer),
                   db: Session = Depends(get_db)) -> User | None:
    if not creds:
        return None
    try:
        payload = jwt.decode(creds.credentials, get_settings().SECRET_KEY, algorithms=["HS256"])
        return db.query(User).filter(User.id == int(payload["sub"])).first()
    except Exception:
        return None


def _purchase_txns(db: Session) -> list[list[int]]:
    txns: dict[int, list[int]] = {}
    for oi in db.query(OrderItem).all():
        txns.setdefault(oi.order_id, []).append(oi.product_id)
    return [sorted(set(t)) for t in txns.values() if t]


def _view_txns(db: Session) -> list[list[int]]:
    by_user: dict[str, list[int]] = {}
    for v in db.query(ProductView).all():
        by_user.setdefault(f"u{v.user_id}" if v.user_id else f"a{v.id}", []).append(v.product_id)
    return [sorted(set(t)) for t in by_user.values() if t]


def _popular(db: Session, category_id: int | None, limit: int,
             exclude: set[int] | None = None) -> list[int]:
    q = db.query(OrderItem.product_id, func.sum(OrderItem.quantity).label("q"))
    if category_id:
        q = q.join(Product, Product.id == OrderItem.product_id
                   ).filter(Product.category_id == category_id)
    rows = q.group_by(OrderItem.product_id).order_by(func.sum(OrderItem.quantity).desc()
                                                     ).limit(limit * 2).all()
    out = [pid for pid, _ in rows if pid not in (exclude or set())]
    if len(out) < limit:  # cold start: newest active products
        extra = db.query(Product.id).filter(Product.is_active == True,  # noqa: E712
                                            Product.category_id == category_id if category_id else True
                                            ).order_by(Product.id.desc()).limit(limit).all()
        out += [pid for (pid,) in extra if pid not in out and pid not in (exclude or set())]
    return out[:limit]


@router.post("/products/{product_id}/view", status_code=204)
def log_view(product_id: int, db: Session = Depends(get_db),
             user: User | None = Depends(_optional_user)):
    if not db.query(Product).filter(Product.id == product_id).first():
        raise HTTPException(404, "Product not found")
    db.add(ProductView(product_id=product_id, user_id=user.id if user else None))
    db.commit()
    return None


@router.get("/products/{product_id}/recommendations")
def for_product(product_id: int, kind: str = Query("bought_together",
                                                   pattern="^(bought_together|also_viewed)$"),
                limit: int = Query(10, ge=1, le=20), db: Session = Depends(get_db)):
    p = db.query(Product).filter(Product.id == product_id).first()
    if not p:
        raise HTTPException(404, "Product not found")
    key = cache.cache_key("recs", kind, str(product_id), str(limit))
    if (hit := cache.cache_get(key)) is not None:
        return hit
    txns = _purchase_txns(db) if kind == "bought_together" else _view_txns(db)
    recs = [pid for pid, _ in similar_items(product_id, txns, limit=limit)]
    if not recs:  # cold start
        recs = _popular(db, p.category_id, limit, exclude={product_id})
    out = {"product_id": product_id, "kind": kind, "items": recs}
    cache.cache_set(key, out, ttl=300)
    return out


@router.get("/users/me/recommendations")
def for_me(limit: int = Query(10, ge=1, le=20), user: User = Depends(get_current_user),
           db: Session = Depends(get_db)):
    bought = sorted({oi.product_id for oi in db.query(OrderItem).join(Order).filter(
        Order.user_id == user.id).all()})
    if not bought:  # cold start: category populars
        txns: list[list[int]] = []
    else:
        txns = _purchase_txns(db)
    recs = [pid for pid, _ in personal_for(bought, txns, limit=limit)] if bought else []
    if not recs:
        recs = _popular(db, None, limit, exclude=set(bought))
    return {"user_id": user.id, "items": recs}
