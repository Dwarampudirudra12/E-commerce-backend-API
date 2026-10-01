"""Order, checkout + state machine (doc 3.3 — core module).

POST /orders (Idempotency-Key): cart -> price re-validation -> row locking ->
atomic reservation (409 + rollback when short) -> totals -> fraud scoring
(>0.70 => ON_HOLD) -> payment intent -> PENDING_PAYMENT. Retried keys return
the ORIGINAL order: no duplicate orders, no double charges.
"""
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core import metrics
from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.cart_order import Cart, CartItem, Order, OrderItem, OrderStatusHistory
from app.models.catalog import Inventory, Product, ProductVariant
from app.models.observability import MlPrediction
from app.models.payment import DiscountCode, Payment
from app.models.user import Address, User
from app.schemas.order import CheckoutIn, OrderOut, StatusPatch
from app.services import fraud as fraud_svc
from app.services.activity import audit, notify
from app.services.inventory import (InsufficientStock, commit_stock, lock_inventory_rows,
                                    release_stock, reserve_stock)
from app.services.payment_gateway import create_intent
from app.services.pricing import calc_totals

router = APIRouter(prefix="/orders", tags=["orders"])

TRANSITIONS: dict[str, list[str]] = {
    "CREATED": ["PENDING_PAYMENT", "CANCELLED", "ON_HOLD"],
    "PENDING_PAYMENT": ["CANCELLED", "ON_HOLD"],
    "ON_HOLD": ["PENDING_PAYMENT", "CANCELLED"],
    "PAID": ["PACKED", "CANCELLED", "REFUNDED"],
    "PACKED": ["SHIPPED", "CANCELLED"],
    "SHIPPED": ["DELIVERED"],
    "DELIVERED": [], "CANCELLED": [], "REFUNDED": [],
}


def _order_out(order: Order, db: Session) -> dict:
    items = db.query(OrderItem).filter(OrderItem.order_id == order.id).all()
    d = {c.name: getattr(order, c.name) for c in order.__table__.columns}
    for k in ("subtotal", "tax", "shipping", "discount", "total"):
        d[k] = float(d[k])
    d["risk_score"] = float(order.risk_score) if order.risk_score is not None else None
    d["items"] = [{"product_id": i.product_id, "variant_id": i.variant_id, "quantity": i.quantity,
                   "unit_price": float(i.unit_price), "subtotal": float(i.subtotal)} for i in items]
    return d


def _fraud_features(db: Session, user: User, *, total: float, item_count: int,
                    discount_ratio: float, shipping: dict) -> dict:
    now = datetime.now(timezone.utc)
    age_days = (now - user.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 86400
    last = db.query(Order).filter(Order.user_id == user.id).order_by(Order.id.desc()).first()
    hours_since = ((now - last.created_at.replace(tzinfo=timezone.utc)).total_seconds() / 3600
                   if last else 24 * 365)
    hour_ago = now - timedelta(hours=1)
    velocity = db.query(Order).filter(Order.user_id == user.id,
                                      Order.created_at >= hour_ago).count()
    failed = db.query(Payment).join(Order).filter(
        Order.user_id == user.id, Payment.status == "FAILED").count()
    default_addr = db.query(Address).filter(Address.user_id == user.id,
                                            Address.is_default == True).first()  # noqa: E712
    mismatch = bool(default_addr and shipping.get("country")
                    and default_addr.country
                    and shipping.get("country") != default_addr.country)
    return {"amount": total, "item_count": item_count, "discount_ratio": discount_ratio,
            "account_age_days": round(age_days, 2), "hours_since_last_order": round(hours_since, 2),
            "orders_last_hour": velocity, "failed_payments": failed + user.failed_logins,
            "country_mismatch": int(mismatch), "new_device": int(age_days < 1),
            "hour_of_day": now.hour}


def _release_order_stock(db: Session, order: Order, *, was_paid: bool) -> None:
    for i in db.query(OrderItem).filter(OrderItem.order_id == order.id).all():
        if was_paid:  # stock was committed: put units back on hand
            inv = db.query(Inventory).filter(Inventory.product_id == i.product_id,
                                             Inventory.variant_id == i.variant_id).first()
            if inv:
                inv.on_hand += i.quantity
                inv.version += 1
        else:
            release_stock(db, product_id=i.product_id, variant_id=i.variant_id, qty=i.quantity)


@router.post("", response_model=OrderOut)
def checkout(data: CheckoutIn, idempotency_key: str | None = Header(None, alias="Idempotency-Key"),
             user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    if not idempotency_key:
        raise HTTPException(422, "Idempotency-Key header is required")
    # Retried request -> original order (M2 criterion #3).
    if (existing := db.query(Order).filter(Order.idempotency_key == idempotency_key).first()):
        metrics.ORDERS_CREATED.labels(outcome="idempotent_hit").inc()
        return _order_out(existing, db)

    cart = db.query(Cart).filter(Cart.user_id == user.id).first()
    items = db.query(CartItem).filter(CartItem.cart_id == cart.id).all() if cart else []
    if not items:
        raise HTTPException(400, "Cart is empty")

    # Price re-validation against live catalog.
    for it in items:
        p = db.query(Product).filter(Product.id == it.product_id).first()
        if not p or not p.is_active:
            raise HTTPException(409, f"Product {it.product_id} unavailable")
        price = float(p.price)
        if it.variant_id:
            v = db.query(ProductVariant).filter(ProductVariant.id == it.variant_id).first()
            if v and v.price_override is not None:
                price = float(v.price_override)
        it.unit_price = price

    lock_inventory_rows(db, [i.product_id for i in items])
    reserved: list[CartItem] = []
    try:
        for it in items:
            reserve_stock(db, product_id=it.product_id, variant_id=it.variant_id, qty=it.quantity)
            reserved.append(it)
    except InsufficientStock:
        for it in reserved:
            release_stock(db, product_id=it.product_id, variant_id=it.variant_id, qty=it.quantity)
        db.rollback()
        metrics.ORDERS_CREATED.labels(outcome="conflict").inc()
        raise HTTPException(409, "Insufficient stock — nothing was reserved")

    subtotal = round(sum(float(i.unit_price) * i.quantity for i in items), 2)
    code = None
    if data.discount_code:
        code = db.query(DiscountCode).filter(DiscountCode.code == data.discount_code).first()
        if not code or not code.is_active:
            for it in items:
                release_stock(db, product_id=it.product_id, variant_id=it.variant_id, qty=it.quantity)
            db.rollback()
            raise HTTPException(400, "Invalid discount code")
    totals = calc_totals(subtotal, code)
    item_count = sum(i.quantity for i in items)
    discount_ratio = round(totals["discount"] / subtotal, 4) if subtotal else 0.0

    order = Order(user_id=user.id, status="CREATED", idempotency_key=idempotency_key,
                  shipping_address=data.shipping_address, **totals)
    db.add(order)
    try:
        db.flush()
    except IntegrityError:  # concurrent same-key race -> return original
        db.rollback()
        existing = db.query(Order).filter(Order.idempotency_key == idempotency_key).first()
        if existing is None:
            raise  # genuine constraint failure — do not mask it
        metrics.ORDERS_CREATED.labels(outcome="idempotent_hit").inc()
        return _order_out(existing, db)
    order.order_number = f"ORD-{datetime.now(timezone.utc).year}-{order.id:06d}"
    for it in items:
        db.add(OrderItem(order_id=order.id, product_id=it.product_id, variant_id=it.variant_id,
                         quantity=it.quantity, unit_price=it.unit_price,
                         subtotal=round(float(it.unit_price) * it.quantity, 2)))
    db.add(OrderStatusHistory(order_id=order.id, from_status="", to_status="CREATED",
                              changed_by=user.id))
    if code:
        code.used_count += 1

    # Fraud scoring (doc 3.4) before payment capture.
    feats = _fraud_features(db, user, total=totals["total"], item_count=item_count,
                            discount_ratio=discount_ratio, shipping=data.shipping_address or {})
    score, f_label, factors = fraud_svc.score_order(feats)
    order.risk_score = score
    db.add(MlPrediction(model_name="fraud", model_version="m2-baseline-1",
                        entity_type="order", entity_id=str(order.id),
                        score=score, label=f_label, top_factors=factors))
    metrics.FRAUD_SCORED.labels(label=f_label).inc()

    if f_label == "high":
        order.status = "ON_HOLD"
        db.add(OrderStatusHistory(order_id=order.id, from_status="CREATED",
                                  to_status="ON_HOLD", changed_by=None,
                                  note=f"fraud score {score}: {', '.join(factors)}"))
        notify(db, user_id=None, type="high_risk_order", payload={"order_id": order.id, "score": score})
        audit(db, user_id=user.id, action="order.fraud_hold", entity_type="order",
              entity_id=str(order.id))
        metrics.ORDERS_CREATED.labels(outcome="held_fraud").inc()
    else:
        intent = create_intent(order_id=order.id, amount=totals["total"],
                               idempotency_key=idempotency_key)
        db.add(Payment(order_id=order.id, gateway_ref=intent["gateway_ref"],
                       amount=totals["total"], status="PENDING"))
        order.status = "PENDING_PAYMENT"
        db.add(OrderStatusHistory(order_id=order.id, from_status="CREATED",
                                  to_status="PENDING_PAYMENT", changed_by=user.id))
        audit(db, user_id=user.id, action="order.created", entity_type="order",
              entity_id=str(order.id))
        metrics.ORDERS_CREATED.labels(outcome="created").inc()

    for it in items:
        db.delete(it)
    notify(db, user_id=user.id, type="order_created", channel="both", email=user.email,
           subject=f"Order {order.order_number} received",
           body=f"Total ${totals['total']}, status {order.status}",
           payload={"order_id": order.id, "status": order.status})
    db.commit()
    db.refresh(order)
    return _order_out(order, db)


@router.get("", response_model=dict)
def list_orders(page: int = 1, page_size: int = 20,
                user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Order)
    if user.role == "CUSTOMER":
        q = q.filter(Order.user_id == user.id)
    elif user.role == "SELLER":
        my_pids = [p.id for p in db.query(Product).filter(Product.seller_id == user.id).all()]
        oids = [oi.order_id for oi in db.query(OrderItem).filter(
            OrderItem.product_id.in_(my_pids)).all()] if my_pids else []
        q = q.filter(Order.id.in_(oids)) if oids else q.filter(Order.id == -1)
    # SUPPORT / ADMIN see all.
    q = q.order_by(Order.id.desc())
    total = q.count()
    return {"items": [_order_out(o, db) for o in q.offset((page - 1) * page_size).limit(page_size).all()],
            "total": total, "page": page, "page_size": page_size}


@router.get("/{order_id}", response_model=OrderOut)
def get_order(order_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if user.role == "CUSTOMER" and order.user_id != user.id:
        raise HTTPException(403, "Not your order")
    return _order_out(order, db)


@router.patch("/{order_id}/status", response_model=OrderOut)
def change_status(order_id: int, data: StatusPatch,
                  user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    dest = data.to_status.upper()
    if dest == "PAID":
        raise HTTPException(422, "PAID is set by verified payment webhooks only")
    if dest not in TRANSITIONS.get(order.status, []):
        raise HTTPException(422, f"Illegal transition {order.status} -> {dest}")

    # Permissions (doc permission matrix).
    if user.role == "CUSTOMER":
        if order.user_id != user.id or dest != "CANCELLED" or order.status == "SHIPPED":
            raise HTTPException(403, "Customers may only cancel their own pre-shipment orders")
    elif user.role == "SELLER":
        if dest not in ("PACKED", "SHIPPED"):
            raise HTTPException(403, "Sellers may only pack/ship")
    elif user.role not in ("SUPPORT", "ADMIN"):
        raise HTTPException(403, "Not allowed")

    if dest == "CANCELLED":
        paid = db.query(Payment).filter(Payment.order_id == order.id,
                                        Payment.status == "SUCCEEDED").first() is not None
        _release_order_stock(db, order, was_paid=paid)
    if dest == "PENDING_PAYMENT" and order.status == "ON_HOLD":
        # Manual-review approval: create the payment intent now.
        intent = create_intent(order_id=order.id, amount=float(order.total),
                               idempotency_key=f"{order.idempotency_key}-approved")
        if not db.query(Payment).filter(Payment.order_id == order.id).first():
            db.add(Payment(order_id=order.id, gateway_ref=intent["gateway_ref"],
                           amount=order.total, status="PENDING"))
    db.add(OrderStatusHistory(order_id=order.id, from_status=order.status,
                              to_status=dest, changed_by=user.id, note=data.note))
    order.status = dest
    audit(db, user_id=user.id, action=f"order.status_{dest.lower()}",
          entity_type="order", entity_id=str(order.id))
    db.commit()
    db.refresh(order)
    return _order_out(order, db)
