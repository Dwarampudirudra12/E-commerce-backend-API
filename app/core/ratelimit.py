"""Rate limiting (M4 security): per-IP token buckets on sensitive surfaces.

- /auth/* (login/register/token): 10/min — brute-force protection.
- /payments/webhook: 60/min — gateway storm protection.
Backend: Redis INCR+EXPIRE when reachable, else process-local memory.
Skipped when disabled or APP_ENV=test (suite makes hundreds of calls).
"""
import logging
import time

log = logging.getLogger(__name__)
_memory: dict[str, list[float]] = {}


def _redis():
    try:
        import redis
        from app.core.config import get_settings
        c = redis.Redis.from_url(get_settings().REDIS_URL, socket_connect_timeout=1,
                                 socket_timeout=1)
        c.ping()
        return c
    except Exception:
        return None


def _memory_allow(key: str, limit: int, window: int) -> bool:
    now = time.time()
    hits = [t for t in _memory.get(key, []) if now - t < window]
    if len(hits) >= limit:
        _memory[key] = hits
        return False
    _memory[key] = hits + [now]
    return True


def is_allowed(ip: str, bucket: str, limit: int, window: int = 60) -> bool:
    key = f"rl:{bucket}:{ip}"
    c = _redis()
    if c is not None:
        try:
            n = c.incr(key)
            if n == 1:
                c.expire(key, window)
            return n <= limit
        except Exception:
            pass
    return _memory_allow(key, limit, window)


def bucket_for(path: str) -> tuple[str, int] | None:
    from app.core.config import get_settings
    s = get_settings()
    if path.startswith("/api/v1/auth/"):
        return ("auth", s.RATE_LIMIT_AUTH_PER_MIN)
    if path == "/api/v1/payments/webhook":
        return ("webhook", s.RATE_LIMIT_WEBHOOK_PER_MIN)
    return None


def reset_memory() -> None:
    _memory.clear()
