"""Liveness / readiness (doc 3.5). Real Prometheus exposition lives at /metrics (main)."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.orm import Session

from app.core import cache
from app.db.session import get_db

router = APIRouter(tags=["health"])


@router.get("/health/live")
def live():
    return {"status": "ok"}


@router.get("/health/ready")
def ready(db: Session = Depends(get_db)):
    checks = {"database": "down", "redis": "down"}
    try:
        db.execute(text("SELECT 1"))
        checks["database"] = "up"
    except Exception:
        pass
    if cache.cache_get("__ping__") is not None or _redis_ping():
        checks["redis"] = "up"
    ok = checks["database"] == "up"
    return {"ready": ok, "checks": checks}


def _redis_ping() -> bool:
    try:
        import redis
        from app.core.config import get_settings
        redis.Redis.from_url(get_settings().REDIS_URL,
                             socket_connect_timeout=1).ping()
        return True
    except Exception:
        return False
