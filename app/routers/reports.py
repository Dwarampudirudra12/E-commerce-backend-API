"""Basic sales report (doc 3.5/M2): revenue, orders, AOV, by-status. Admin only
in M2; per-seller scoping arrives with the M3 dashboard."""
from datetime import datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.core.deps import RequireAdmin
from app.db.session import get_db
from app.models.cart_order import Order
from app.models.user import User

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/sales/summary")
def sales_summary(from_date: str | None = Query(None), to_date: str | None = Query(None),
                  admin: User = Depends(RequireAdmin), db: Session = Depends(get_db)):
    q = db.query(Order).filter(Order.status.notin_(["CANCELLED"]))
    if from_date:
        q = q.filter(Order.created_at >= datetime.fromisoformat(from_date))
    if to_date:
        q = q.filter(Order.created_at <= datetime.fromisoformat(to_date))
    orders = q.all()
    revenue = round(sum(float(o.total) for o in orders if o.status != "REFUNDED"), 2)
    by_status: dict[str, int] = {}
    for o in orders:
        by_status[o.status] = by_status.get(o.status, 0) + 1
    return {"revenue": revenue, "orders": len(orders),
            "average_order_value": round(revenue / len(orders), 2) if orders else 0.0,
            "by_status": by_status}
