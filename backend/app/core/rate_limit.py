"""In-process sliding-window rate limiting.

Counters live in this process only. With several workers each one keeps its own counts, so the
effective limit grows with the worker count. Replace this with a Redis-backed limiter before
running more than one replica.
"""

import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable

_SWEEP_THRESHOLD = 10_000


class RateLimiter:
    def __init__(self, clock: Callable[[], float] = time.monotonic) -> None:
        self._clock = clock
        self._events: dict[str, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    def check(self, key: str, *, limit: int, window_seconds: float) -> float | None:
        """Record one attempt for `key`.

        Returns None when the attempt is allowed. Otherwise returns the seconds until the
        next attempt would be allowed, and the attempt is not recorded.
        """
        now = self._clock()
        with self._lock:
            if len(self._events) > _SWEEP_THRESHOLD:
                self._sweep(now, window_seconds)
            events = self._events[key]
            while events and now - events[0] >= window_seconds:
                events.popleft()
            if len(events) >= limit:
                return window_seconds - (now - events[0])
            events.append(now)
            return None

    def _sweep(self, now: float, window_seconds: float) -> None:
        """Drop keys whose newest event has left the window, so memory does not grow forever."""
        stale = [key for key, events in self._events.items() if now - events[-1] >= window_seconds]
        for key in stale:
            del self._events[key]
