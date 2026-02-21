from __future__ import annotations

import time
from unittest.mock import patch

from app.services.rate_limiter import SlidingWindowRateLimiter


class TestSlidingWindowRateLimiter:
    """Tests for SlidingWindowRateLimiter."""

    def test_requests_within_limit_pass_immediately(self) -> None:
        """Five calls against a limit of 5 should all return without blocking."""
        limiter = SlidingWindowRateLimiter(requests_per_minute=5)
        start = time.monotonic()
        for _ in range(5):
            limiter.acquire()
        elapsed = time.monotonic() - start
        # Should complete well under 1 second — no sleeping involved
        assert elapsed < 1.0

    def test_limiter_tracks_request_count(self) -> None:
        """After N successful acquire() calls the internal deque holds N timestamps."""
        limiter = SlidingWindowRateLimiter(requests_per_minute=10)
        for _ in range(7):
            limiter.acquire()
        assert len(limiter._timestamps) == 7

    def test_high_rpm_allows_many_calls(self) -> None:
        """With rpm=1000, 50 rapid calls should all succeed without blocking."""
        limiter = SlidingWindowRateLimiter(requests_per_minute=1000)
        start = time.monotonic()
        for _ in range(50):
            limiter.acquire()
        elapsed = time.monotonic() - start
        assert elapsed < 1.0
        assert len(limiter._timestamps) == 50

    def test_window_starts_fresh(self) -> None:
        """A brand-new limiter with rpm=2 allows exactly 2 immediate calls."""
        limiter = SlidingWindowRateLimiter(requests_per_minute=2)
        limiter.acquire()
        limiter.acquire()
        assert len(limiter._timestamps) == 2

    def test_full_window_blocks_until_slot_available(self) -> None:
        """When the window is full, the next call should wait until a slot opens.

        We mock time.time to jump 61 s into the future so the test never
        actually sleeps, and we replace time.sleep with a no-op so the
        limiter's internal retry loop resolves immediately.
        """
        limiter = SlidingWindowRateLimiter(requests_per_minute=1)
        limiter.acquire()  # fills the single-slot window

        future_time = time.time() + 61
        with patch("app.services.rate_limiter.time") as mock_time:
            mock_time.time.return_value = future_time
            mock_time.sleep = lambda _: None  # no-op — never actually sleeps
            limiter.acquire()  # window cleared; should succeed

        # Only the second acquire's timestamp survives in the deque
        assert len(limiter._timestamps) == 1
