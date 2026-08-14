"""Small Redis-backed rate limiter with an in-memory development fallback."""

from __future__ import annotations

import threading
import time
from collections import defaultdict, deque
from typing import Callable

from fastapi import HTTPException, Request


def _parse_limit(value: str) -> tuple[int, int]:
    count_text, period = value.split("/", 1)
    count = int(count_text)
    seconds = {"second": 1, "minute": 60, "hour": 3600}[period.rstrip("s")]
    if count < 1:
        raise ValueError("rate limit count must be positive")
    return count, seconds


class RateLimiter:
    def __init__(self, redis_url: str = "") -> None:
        self.redis_url = redis_url
        self._lock = threading.RLock()
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._redis = None
        if redis_url:
            try:
                import redis

                self._redis = redis.Redis.from_url(redis_url, decode_responses=True)
                self._redis.ping()
            except Exception:
                self._redis = None

    def allow(self, key: str, limit: int, window_seconds: int) -> tuple[bool, int]:
        now = time.monotonic()
        if self._redis is not None:
            redis_key = f"living-objects:rate:{key}"
            try:
                count = int(self._redis.incr(redis_key))
                if count == 1:
                    self._redis.expire(redis_key, window_seconds)
                ttl = max(1, int(self._redis.ttl(redis_key)))
                return count <= limit, ttl
            except Exception:
                pass
        with self._lock:
            events = self._events[key]
            cutoff = now - window_seconds
            while events and events[0] <= cutoff:
                events.popleft()
            if len(events) >= limit:
                retry_after = max(1, int(events[0] + window_seconds - now))
                return False, retry_after
            events.append(now)
            return True, window_seconds

    def dependency(self, policy: str) -> Callable[[Request], None]:
        limit, window = _parse_limit(policy)

        def check(request: Request) -> None:
            address = request.client.host if request.client else "unknown"
            key = f"{address}:{request.method}:{request.url.path}:{policy}"
            allowed, retry_after = self.allow(key, limit, window)
            if not allowed:
                raise HTTPException(
                    status_code=429,
                    detail="rate limit exceeded",
                    headers={"Retry-After": str(retry_after)},
                )

        return check


_limiter = RateLimiter()


_enabled = True


def configure_rate_limiter(redis_url: str, *, enabled: bool = True) -> RateLimiter:
    global _limiter
    global _enabled
    _limiter = RateLimiter(redis_url)
    _enabled = enabled
    return _limiter


def rate_limit_dependency(policy: str) -> Callable[[Request], None]:
    limit, window = _parse_limit(policy)

    def check(request: Request) -> None:
        if not _enabled:
            return
        address = request.client.host if request.client else "unknown"
        key = f"{address}:{request.method}:{request.url.path}:{policy}"
        allowed, retry_after = _limiter.allow(key, limit, window)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="rate limit exceeded",
                headers={"Retry-After": str(retry_after)},
            )

    return check


__all__ = ["RateLimiter", "configure_rate_limiter", "rate_limit_dependency"]
