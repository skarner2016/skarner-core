import time

import pytest

from skarner.core.ratelimit import MemoryRateLimiter, RateLimitResult


@pytest.fixture
def limiter():
    return MemoryRateLimiter()


def test_result_type(limiter):
    result = limiter.limit("user:1:/feed", rate=5, per_seconds=10)
    assert isinstance(result, RateLimitResult)


def test_allowed_within_rate(limiter):
    for _ in range(3):
        assert limiter.limit("user:1:/feed", rate=3, per_seconds=10).allowed


def test_blocked_when_rate_exceeded(limiter):
    for _ in range(3):
        limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    result = limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    assert not result.allowed
    assert result.remaining == 0


def test_remaining_decrements(limiter):
    r1 = limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    r2 = limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    r3 = limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    assert r1.remaining == 2
    assert r2.remaining == 1
    assert r3.remaining == 0


def test_different_users_have_independent_quota(limiter):
    for _ in range(3):
        limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    result = limiter.limit("user:2:/feed", rate=3, per_seconds=10)
    assert result.allowed


def test_different_endpoints_have_independent_quota(limiter):
    for _ in range(3):
        limiter.limit("user:1:/feed", rate=3, per_seconds=10)
    result = limiter.limit("user:1:/profile", rate=3, per_seconds=10)
    assert result.allowed


def test_quota_recovers_after_window(limiter):
    for _ in range(3):
        limiter.limit("user:1:/feed", rate=3, per_seconds=1)
    assert not limiter.limit("user:1:/feed", rate=3, per_seconds=1).allowed

    time.sleep(1.1)
    assert limiter.limit("user:1:/feed", rate=3, per_seconds=1).allowed


def test_thread_safety(limiter):
    import threading

    results = []
    lock = threading.Lock()

    def call():
        r = limiter.limit("user:1:/feed", rate=5, per_seconds=10)
        with lock:
            results.append(r.allowed)

    threads = [threading.Thread(target=call) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()

    assert results.count(True) == 5
    assert results.count(False) == 5
