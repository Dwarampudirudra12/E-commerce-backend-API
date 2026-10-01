"""Liveness / readiness + Prometheus metrics stub (doc 3.5)."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    checks = {"database": "down", "redis": "degraded-m1"}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        pass
    # Redis check wired in M2 (needs live redis); M1 reports degraded, not down.
    try:
        import redis  # noqa
    except Exception:
        pass
    ok = checks["database"] == "up"
    return {"ready": ok, "checks": checks}


@router.get("/metrics", include_in_schema=False)
def metrics():
    return "# M1 metrics stub — Prometheus wired in M2\nhttp_requests_total 0\n"
