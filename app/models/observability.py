"""Notifications, audit trail (append-only), ML predictions, demand history, views."""
from datetime import date as date_type
from datetime import datetime
from sqlalchemy import JSON, Boolean, Date, DateTime, Float, ForeignKey, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True)
    type: Mapped[str] = mapped_column(String(64), index=True)  # e.g. order_confirmed
    channel: Mapped[str] = mapped_column(String(32))  # email | in_app | both
    status: Mapped[str] = mapped_column(String(32), default="QUEUED", index=True)
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, index=True)  # M3 in-app inbox
    payload: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class AuditLog(Base):
    """Append-only: no UPDATE/DELETE routes ever touch this table."""
    __tablename__ = "audit_logs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True, index=True)
    action: Mapped[str] = mapped_column(String(128), index=True)
    entity_type: Mapped[str] = mapped_column(String(64), index=True)
    entity_id: Mapped[str | None] = mapped_column(String(64), nullable=True)
    meta: Mapped[dict | None] = mapped_column("metadata", JSON, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), index=True)


class MlPrediction(Base):
    __tablename__ = "ml_predictions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    model_name: Mapped[str] = mapped_column(String(64), index=True)  # fraud|forecast|recommend
    model_version: Mapped[str] = mapped_column(String(32))
    entity_type: Mapped[str] = mapped_column(String(32))  # order|product
    entity_id: Mapped[str] = mapped_column(String(64), index=True)
    score: Mapped[float] = mapped_column(Float)
    label: Mapped[str | None] = mapped_column(String(32), nullable=True)
    top_factors: Mapped[dict | list | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class DemandHistory(Base):
    """Daily units sold per product — feeds forecasting (M3). Backfilled by seed."""
    __tablename__ = "demand_history"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    day: Mapped[date_type] = mapped_column(Date, index=True)
    qty: Mapped[int] = mapped_column(Integer, default=0)


class ProductView(Base):
    """Lightweight view log — feeds 'also viewed' recommendations (M3)."""
    __tablename__ = "product_views"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"),
                                                nullable=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
