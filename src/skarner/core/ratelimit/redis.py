from .base import BaseRateLimiter, RateLimitResult

__all__ = ["RedisRateLimiter"]

# Sliding-window via a sorted set.
# KEYS[1]: redis key  ARGV[1]: now (ms)  ARGV[2]: window (ms)  ARGV[3]: rate  ARGV[4]: ttl (s)
_SCRIPT = """
local key     = KEYS[1]
local now     = tonumber(ARGV[1])
local window  = tonumber(ARGV[2])
local rate    = tonumber(ARGV[3])
local ttl     = tonumber(ARGV[4])

redis.call('ZREMRANGEBYSCORE', key, '-inf', now - window)
local count = redis.call('ZCARD', key)

if count >= rate then
    return {0, 0}
end

redis.call('ZADD', key, now, now)
redis.call('EXPIRE', key, ttl)
return {1, rate - count - 1}
"""


class RedisRateLimiter(BaseRateLimiter):
    """Sliding-window rate limiter backed by Redis sorted sets.

    Args:
        redis: A redis-py client instance (sync).
    """

    def __init__(self, redis) -> None:
        self._redis = redis
        self._script = redis.register_script(_SCRIPT)

    def limit(self, key: str, rate: int, per_seconds: int) -> RateLimitResult:
        now_ms = int(__import__("time").time() * 1000)
        window_ms = per_seconds * 1000
        allowed, remaining = self._script(
            keys=[key],
            args=[now_ms, window_ms, rate, per_seconds + 1],
        )
        return RateLimitResult(allowed=bool(allowed), remaining=int(remaining))
