"""A small in-memory limiter that slows down password guessing.

How it works: every FAILED sign-in is remembered for a time window. When one key
(e-mail + address, or just the address) has too many recent failures, further
attempts are refused with HTTP 429 until the oldest failure expires.

Limits of this design (be honest about them in interviews):
* It lives in the server's memory, so it resets when the server restarts and is not
  shared between several server processes. A production deployment would keep the
  counters in Redis.
* The "address" is what the server sees. Behind a reverse proxy that is the proxy's
  address unless the proxy is configured to pass the real client address on.
"""
from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque

from fastapi import HTTPException

from app.core.config import settings


class FailureLimiter:
    def __init__(self, max_failures: int, window_seconds: int, clock=time.monotonic):
        self.max_failures = max_failures
        self.window = window_seconds
        self._clock = clock
        self._hits: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def _prune(self, key: str, now: float) -> deque:
        hits = self._hits[key]
        while hits and now - hits[0] >= self.window:
            hits.popleft()
        if not hits:
            self._hits.pop(key, None)
        return hits

    def seconds_until_allowed(self, key: str) -> int:
        with self._lock:
            now = self._clock()
            hits = self._prune(key, now)
            if len(hits) < self.max_failures:
                return 0
            return max(1, math.ceil(hits[0] + self.window - now))

    def record(self, key: str) -> None:
        with self._lock:
            self._hits[key].append(self._clock())

    def reset(self, key: str) -> None:
        with self._lock:
            self._hits.pop(key, None)

    def clear(self) -> None:
        with self._lock:
            self._hits.clear()

    def check(self, key: str, what: str = "sign-in") -> None:
        wait = self.seconds_until_allowed(key)
        if wait:
            minutes = math.ceil(wait / 60)
            raise HTTPException(
                status_code=429,
                detail=f"Too many {what} attempts. Please try again in {minutes} minute{'s' if minutes != 1 else ''}.",
                headers={"Retry-After": str(wait)},
            )


window = settings.login_window_minutes * 60
login_limiter = FailureLimiter(settings.login_max_failures, window)          # per e-mail + address
ip_limiter = FailureLimiter(settings.login_max_failures_per_ip, window)      # per address (e-mail spraying)
register_limiter = FailureLimiter(settings.register_max_per_hour, 3600)      # account creation per address
need_limiter = FailureLimiter(settings.need_max_per_hour, 3600)           # AI need analyses per farmer
upload_limiter = FailureLimiter(settings.upload_max_per_hour, 3600)         # file uploads per farmer
ALL_LIMITERS = (login_limiter, ip_limiter, register_limiter, need_limiter, upload_limiter)
