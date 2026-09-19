"""Minimal in-process sliding-window rate limiter (docs/12 §2 — rate-limit-ready).

Single-process only; adequate for Phase 1 / district-pilot volume.
Distributed limiting (Redis) — TODO — FUTURE PHASE.
Global per-IP limits remain the reverse proxy's job (docs/15).
"""

import time
from collections import defaultdict, deque


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._hits: dict[str, deque[float]] = defaultdict(deque)

    def check(self, key: str) -> bool:
        """Record a hit for `key`; return True if within the limit, else False."""
        now = time.monotonic()
        window_start = now - self.window_seconds
        hits = self._hits[key]
        while hits and hits[0] < window_start:
            hits.popleft()
        if len(hits) >= self.max_requests:
            return False
        hits.append(now)
        return True

    def reset(self) -> None:
        """Test hook: clear all windows."""
        self._hits.clear()
