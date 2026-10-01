"""Audit trail + notification helpers (doc 3.5/3.7). Every order/payment state
change writes an audit row (append-only) and a notification row; email goes
through the console mock in M2, real SMTP/SendGrid in M3."""
from sqlalchemy.orm import Session

from app.models.observability import AuditLog, Notification
from app.services.email_service import send_email


def audit(db: Session, *, user_id: int | None, action: str,
          entity_type: str = "", entity_id: str | None = None,
          ip: str | None = None, meta: dict | None = None) -> None:
    db.add(AuditLog(user_id=user_id, action=action, entity_type=entity_type,
                    entity_id=entity_id, ip_address=ip, meta=meta))


def notify(db: Session, *, user_id: int | None, type: str, channel: str = "in_app",
           payload: dict | None = None, email: str | None = None,
           subject: str = "", body: str = "") -> None:
    db.add(Notification(user_id=user_id, type=type, channel=channel,
                        status="SENT", payload=payload or {}))
    if email and channel in ("email", "both"):
        send_email(email, subject or type, body or str(payload or {}))
