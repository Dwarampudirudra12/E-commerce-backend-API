"""In-app notification inbox (doc 3.7, M3): list own notifications, mark read."""
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user
from app.db.session import get_db
from app.models.observability import Notification
from app.models.user import User

router = APIRouter(prefix="/notifications", tags=["notifications"])


@router.get("/me")
def my_notifications(unread_only: bool = Query(False),
                     page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
                     user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    q = db.query(Notification).filter(Notification.user_id == user.id
                                      ).order_by(Notification.id.desc())
    if unread_only:
        q = q.filter(Notification.is_read == False)  # noqa: E712
    total = q.count()
    items = q.offset((page - 1) * page_size).limit(page_size).all()
    return {"items": [{"id": n.id, "type": n.type, "channel": n.channel, "status": n.status,
                       "is_read": n.is_read, "payload": n.payload,
                       "created_at": n.created_at.isoformat() if n.created_at else None}
                      for n in items],
            "total": total, "unread": db.query(Notification).filter(
                Notification.user_id == user.id, Notification.is_read == False).count()}  # noqa: E712


@router.patch("/{notif_id}/read")
def mark_read(notif_id: int, user: User = Depends(get_current_user),
              db: Session = Depends(get_db)):
    n = db.query(Notification).filter(Notification.id == notif_id,
                                     Notification.user_id == user.id).first()
    if not n:
        raise HTTPException(404, "Notification not found")
    n.is_read = True
    db.commit()
    return {"ok": True}
