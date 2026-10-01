"""Redis cache wrapper (doc 3.2: hot catalog pages). Degrades gracefully when
Redis is unavailable (tests, local runs without docker) — callers never break."""
import hashlib
import json
import logging

log = logging.getLogger(__name__)
_client = None


def _get_client():
    global _client
    if _client is not None:
        return _client
    try:
        import redis
        from app.core.config import get_settings
        c = redis.Redis.from_url(get_settings().REDIS_URL, socket_connect_timeout=1, socket_timeout=1)
        c.ping()
        _client = c
        return c
    except Exception as e:  # noqa: BLE001 — redis optional in M2
        log.debug("redis unavailable, caching disabled: %s", e)
        _client = False
        return None


def cache_key(*parts: str) -> str:
    raw = ":".join(parts)
    return "ecom:" + hashlib.sha256(raw.encode()).hexdigest()[:32]


def cache_get(key: str):
    c = _get_client()
    if not c:
        return None
    try:
        val = c.get(key)
        return json.loads(val) if val else None
    except Exception:
        return None


def cache_set(key: str, value, ttl: int = 60) -> None:
    c = _get_client()
    if not c:
        return
    try:
        c.setex(key, ttl, json.dumps(value, default=str))
    except Exception:
        pass


def cache_delete_prefix(prefix: str) -> None:
    """Catalog writes call this with 'catalog' to invalidate listings."""
    c = _get_client()
    if not c:
        return
    try:
        for k in c.scan_iter(f"ecom:{prefix}*"):
            c.delete(k)
    except Exception:
        pass


def reset_client() -> None:
    """Tests only — drop cached client so fallback path is exercised."""
    global _client
    _client = None
