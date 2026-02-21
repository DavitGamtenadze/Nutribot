from __future__ import annotations

import time
from collections import deque
from threading import Lock


class SlidingWindowRateLimiter:
    """Simple in-process RPM limiter for demo environments."""

    def __init__(self, requests_per_minute: int) -> None:
        self.requests_per_minute = requests_per_minute
        self._timestamps: deque[float] = deque()
        self._lock = Lock()

    def acquire(self) -> None:
        while True:
            sleep_for = 0.0
            now = time.time()
            with self._lock:
                while self._timestamps and (now - self._timestamps[0]) > 60:
                    self._timestamps.popleft()

                if len(self._timestamps) < self.requests_per_minute:
                    self._timestamps.append(now)
                    return

                oldest = self._timestamps[0]
                sleep_for = max(0.01, 60 - (now - oldest))

            time.sleep(sleep_for)
