from abc import ABC, abstractmethod
from dataclasses import dataclass

__all__ = ["RateLimitResult", "BaseRateLimiter"]


@dataclass(frozen=True)
class RateLimitResult:
    allowed: bool
    remaining: int


class BaseRateLimiter(ABC):
    @abstractmethod
    def limit(self, key: str, rate: int, per_seconds: int) -> RateLimitResult:
        """Check and consume one request quota.

        Args:
            key: Unique identifier, e.g. "user:42:/api/feed".
            rate: Max requests allowed within the window.
            per_seconds: Window size in seconds.
        """
