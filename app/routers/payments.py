"""Payments: intent status, signed webhooks, refunds (doc 3.3/M2).

Webhook contract (mock + stripe): JSON {event_id, type, gateway_ref, amount}
  type: payment.succeeded | payment.failed
Signature: mock -> X-Signature: HMAC-SHA256(body, WEBHOOK_SECRET);
stripe -> Stripe-Signature header verified against STRIPE_WEBHOOK_SECRET.
Deliveries are idempotent via payments.webhook_event_id (UNIQUE): a retried
delivery returns 200 without touching state twice (M2 criterion #3).
"""
from fastapi import APIRouter, Depends, Header, HTTPException, Request
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.core import metrics
from app.core.config import get_settings
from app.core.deps import RequireSupport, get_current_user
from app.db.session import get_db
from app.models.cart_order import Order, OrderItem, OrderStatusHistory
from app.models.catalog import Inventory
from app.models.payment import Payment, Refund
from app.models.user import User
from app.services.activity import audit, notify
from app.services.inventory import commit_stock
from app.services.payment_gateway import (create_refund, verify_mock_signature,
                                          verify_stripe_signature)

router = APIRouter(prefix="/payments", tags=["payments"])


class RefundIn(BaseModel):
    amount: float | None = None
    reason: str = ""


@router.get("/by-order/{order_id}")
def payment_for_order(order_id: int, user: User = Depends(get_current_user),
                      db: Session = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if user.role == "CUSTOMER" and order.user_id != user.id:
        raise HTTPException(403, "Not your order")
    pay = db.query(Payment).filter(Payment.order_id == order_id).first()
    if not pay:
        raise HTTPException(404, "No payment yet")
    return {"id": pay.id, "gateway_ref": pay.gateway_ref, "amount": float(pay.amount),
            "currency": pay.currency, "status": pay.status}


@router.post("/webhook")
async def webhook(request: Request, db: Session = Depends(get_db),
                  x_signature: str | None = Header(None, alias="X-Signature"),
                  stripe_signature: str | None = Header(None, alias="Stripe-Signature")):
    settings = get_settings()
    body = await request.body()
    # Signature verification (M2 criterion #3).
    if stripe_signature and not settings.STRIPE_WEBHOOK_SECRET.startswith("whsec_placeholder"):
        ok = verify_stripe_signature(body, stripe_signature, settings.STRIPE_WEBHOOK_SECRET)
    else:
        ok = verify_mock_signature(body, x_signature or "")
    if not ok:
        metrics.PAYMENT_WEBHOOKS.labels(result="rejected").inc()
        raise HTTPException(400, "Invalid webhook signature")
    try:
        event = await request.json()
    except Exception:
        raise HTTPException(400, "Invalid webhook payload")
    event_id, etype = event.get("event_id"), event.get("type")
    if not event_id or etype not in ("payment.succeeded", "payment.failed"):
        raise HTTPException(400, "Unknown webhook event")

    pay = db.query(Payment).filter(Payment.gateway_ref == event.get("gateway_ref")).first()
    if not pay:
        raise HTTPException(404, "Payment not found")
    if pay.webhook_event_id == event_id or pay.status in ("SUCCEEDED", "FAILED"):
        metrics.PAYMENT_WEBHOOKS.labels(result="duplicate").inc()
        return {"ok": True, "deduped": True}  # retried delivery: no double-apply
    pay.webhook_event_id = event_id

    order = db.query(Order).filter(Order.id == pay.order_id).first()
    if etype == "payment.succeeded":
        pay.status = "SUCCEEDED"
        for i in db.query(OrderItem).filter(OrderItem.order_id == order.id).all():
            commit_stock(db, product_id=i.product_id, variant_id=i.variant_id, qty=i.quantity)
        if order.status in ("PENDING_PAYMENT", "ON_HOLD", "CREATED"):
            db.add(OrderStatusHistory(order_id=order.id, from_status=order.status,
                                      to_status="PAID", note="webhook verified"))
            order.status = "PAID"
        audit(db, user_id=order.user_id, action="payment.succeeded",
              entity_type="order", entity_id=str(order.id))
        notify(db, user_id=order.user_id, type="order_confirmed", channel="both",
               email=db.query(User).filter(User.id == order.user_id).first().email,
               subject=f"Order {order.order_number} paid",
               body=f"Payment of ${float(pay.amount)} confirmed.",
               payload={"order_id": order.id})
        metrics.PAYMENT_WEBHOOKS.labels(result="paid").inc()
    else:
        pay.status = "FAILED"
        audit(db, user_id=order.user_id, action="payment.failed",
              entity_type="order", entity_id=str(order.id))
        notify(db, user_id=order.user_id, type="payment_failed", channel="both",
               email=db.query(User).filter(User.id == order.user_id).first().email,
               subject=f"Payment failed for {order.order_number}",
               body="Please retry checkout — no charge was made.",
               payload={"order_id": order.id})
        metrics.PAYMENT_WEBHOOKS.labels(result="failed").inc()
    db.commit()
    return {"ok": True, "status": pay.status}


@router.post("/{payment_id}/refund")
def refund(payment_id: int, data: RefundIn, user: User = Depends(RequireSupport),
           db: Session = Depends(get_db)):
    settings = get_settings()
    pay = db.query(Payment).filter(Payment.id == payment_id).first()
    if not pay or pay.status != "SUCCEEDED":
        raise HTTPException(400, "Only succeeded payments can be refunded")
    amount = float(data.amount or pay.amount)
    if amount <= 0 or amount > float(pay.amount):
        raise HTTPException(422, "Invalid refund amount")
    if user.role == "SUPPORT" and amount > settings.SUPPORT_REFUND_LIMIT:
        raise HTTPException(403, f"Support limit is ${settings.SUPPORT_REFUND_LIMIT} — admin approval needed")
    gw = create_refund(gateway_ref=pay.gateway_ref, amount=amount)
    refund = Refund(payment_id=pay.id, order_id=pay.order_id, amount=amount,
                    reason=data.reason, status="SUCCEEDED",
                    gateway_refund_id=gw["gateway_refund_id"], approved_by=user.id)
    db.add(refund)
    order = db.query(Order).filter(Order.id == pay.order_id).first()
    if amount >= float(pay.amount) and order.status != "REFUNDED":
        db.add(OrderStatusHistory(order_id=order.id, from_status=order.status,
                                  to_status="REFUNDED", changed_by=user.id, note=data.reason))
        order.status = "REFUNDED"
    # Restock on full refund.
    if amount >= float(pay.amount):
        for i in db.query(OrderItem).filter(OrderItem.order_id == order.id).all():
            inv = db.query(Inventory).filter(Inventory.product_id == i.product_id,
                                             Inventory.variant_id == i.variant_id).first()
            if inv:
                inv.on_hand += i.quantity
                inv.version += 1
    audit(db, user_id=user.id, action="payment.refunded", entity_type="order",
          entity_id=str(order.id))
    notify(db, user_id=order.user_id, type="refund_processed", channel="email",
           email=db.query(User).filter(User.id == order.user_id).first().email,
           subject=f"Refund processed for {order.order_number}",
           body=f"${amount} refunded.", payload={"order_id": order.id, "amount": amount})
    db.commit()
    return {"ok": True, "refund_id": refund.id, "gateway_refund_id": gw["gateway_refund_id"]}
