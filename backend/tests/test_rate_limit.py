"""Sliding-window rate limiter. Uses an injected clock, so no test sleeps."""

from app.core.rate_limit import RateLimiter


class FakeClock:
    def __init__(self) -> None:
        self.now = 1000.0

    def __call__(self) -> float:
        return self.now


def test_attempts_up_to_the_limit_are_allowed() -> None:
    limiter = RateLimiter(clock=FakeClock())
    results = [limiter.check("login:1.2.3.4", limit=3, window_seconds=60) for _ in range(3)]
    assert results == [None, None, None]


def test_attempt_over_the_limit_reports_retry_delay() -> None:
    clock = FakeClock()
    limiter = RateLimiter(clock=clock)
    for _ in range(3):
        limiter.check("login:1.2.3.4", limit=3, window_seconds=60)
    clock.now += 10
    retry_after = limiter.check("login:1.2.3.4", limit=3, window_seconds=60)
    assert retry_after == 50


def test_limit_resets_when_the_window_passes() -> None:
    clock = FakeClock()
    limiter = RateLimiter(clock=clock)
    for _ in range(3):
        limiter.check("login:1.2.3.4", limit=3, window_seconds=60)
    clock.now += 60
    assert limiter.check("login:1.2.3.4", limit=3, window_seconds=60) is None


def test_keys_are_counted_independently() -> None:
    limiter = RateLimiter(clock=FakeClock())
    for _ in range(3):
        limiter.check("login:10.0.0.1", limit=3, window_seconds=60)
    assert limiter.check("login:10.0.0.2", limit=3, window_seconds=60) is None


def test_rejected_attempts_are_not_recorded() -> None:
    clock = FakeClock()
    limiter = RateLimiter(clock=clock)
    for _ in range(3):
        limiter.check("k", limit=3, window_seconds=60)
    for _ in range(5):
        assert limiter.check("k", limit=3, window_seconds=60) is not None
    clock.now += 60
    assert limiter.check("k", limit=3, window_seconds=60) is None
