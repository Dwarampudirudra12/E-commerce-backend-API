"""Read-only operations consoles (M4 frontend integration).

- GET /audit-logs: append-only trail, ADMIN only, optional action filter.
- GET /refunds: refund history, SUPPORT + ADMIN.
- GET /payments: payment ledger, SUPPORT + ADMIN.
All three are pure reads over existing tables — no business-logic change.
"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import RequireAdmin, RequireSupport, get_current_user
from app.db.session import get_db
from app.models.observability import AuditLog
from app.models.payment import Payment, Refund
from app.models.user import User

router = APIRouter(tags=["operations"])


@router.get("/audit-logs", dependencies=[Depends(RequireAdmin)])
def list_audit_logs(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                    action: str | None = Query(None), db: Session = Depends(get_db)):
    q = db.query(AuditLog).order_by(AuditLog.id.desc())
    if action:
        q = q.filter(AuditLog.action.ilike(f"%{action}%"))
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": a.id, "user_id": a.user_id, "action": a.action,
                       "entity_type": a.entity_type, "entity_id": a.entity_id,
                       "ip_address": a.ip_address, "created_at": a.created_at.isoformat()
                       if a.created_at else None} for a in items],
            "total": total, "page": page, "page_size": page_size}


@router.get("/refunds", dependencies=[Depends(RequireSupport)])
def list_refunds(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                 db: Session = Depends(get_db)):
    q = db.query(Refund).order_by(Refund.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": r.id, "payment_id": r.payment_id, "order_id": r.order_id,
                       "amount": float(r.amount), "reason": r.reason, "status": r.status,
                       "gateway_refund_id": r.gateway_refund_id, "approved_by": r.approved_by,
                       "created_at": r.created_at.isoformat() if r.created_at else None}
                      for r in items],
            "total": total, "page": page, "page_size": page_size}


@router.get("/payments", dependencies=[Depends(RequireSupport)])
def list_payments(page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                  db: Session = Depends(get_db)):
    q = db.query(Payment).order_by(Payment.id.desc())
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": p.id, "order_id": p.order_id, "gateway_ref": p.gateway_ref,
                       "amount": float(p.amount), "currency": p.currency, "status": p.status}
                      for p in items],
            "total": total, "page": page, "page_size": page_size}


@router.get("/orders/{order_id}/history")
def order_history(order_id: int, user: User = Depends(get_current_user),
                  db: Session = Depends(get_db)):
    from fastapi import HTTPException
    from app.models.cart_order import Order, OrderStatusHistory
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(404, "Order not found")
    if user.role == "CUSTOMER" and order.user_id != user.id:
        raise HTTPException(403, "Not your order")
    if user.role == "SELLER":
        from app.models.catalog import Product
        from app.models.cart_order import OrderItem
        my_pids = {p.id for p in db.query(Product).filter(Product.seller_id == user.id).all()}
        touches = db.query(OrderItem).filter(OrderItem.order_id == order_id,
                                             OrderItem.product_id.in_(my_pids)).first() if my_pids else None
        if not touches:
            raise HTTPException(403, "Not your order")
    rows = db.query(OrderStatusHistory).filter(
        OrderStatusHistory.order_id == order_id).order_by(OrderStatusHistory.id).all()
    return {"items": [{"from_status": h.from_status, "to_status": h.to_status,
                       "changed_by": h.changed_by, "note": h.note,
                       "created_at": h.created_at.isoformat() if h.created_at else None}
                      for h in rows]}
