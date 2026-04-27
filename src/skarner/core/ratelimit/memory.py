import time
import threading
from collections import deque

from .base import BaseRateLimiter, RateLimitResult

__all__ = ["MemoryRateLimiter"]


class MemoryRateLimiter(BaseRateLimiter):
    """Sliding-window rate limiter backed by in-process memory.

    Not suitable for multi-process deployments — use RedisRateLimiter instead.
    """

    def __init__(self) -> None:
        # key -> deque of request timestamps
        self._windows: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def limit(self, key: str, rate: int, per_seconds: int) -> RateLimitResult:
        now = time.monotonic()
        cutoff = now - per_seconds

        with self._lock:
            window = self._windows.setdefault(key, deque())

            # evict timestamps outside the current window
            while window and window[0] <= cutoff:
                window.popleft()

            if len(window) >= rate:
                return RateLimitResult(allowed=False, remaining=0)

            window.append(now)
            return RateLimitResult(allowed=True, remaining=rate - len(window))
