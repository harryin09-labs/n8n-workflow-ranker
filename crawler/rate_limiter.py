"""
Rate limiter for polite crawling.
Supports synchronous and asynchronous rate limiting with token bucket / sliding interval.
"""

import time
import asyncio
import threading
from typing import Optional


class RateLimiter:
    def __init__(self, requests_per_second: float = 2.0, delay_seconds: Optional[float] = None):
        if delay_seconds is not None:
            self.min_interval = max(0.01, delay_seconds)
        else:
            self.min_interval = 1.0 / max(0.1, requests_per_second)
        self.last_request_time = 0.0
        self._lock = threading.Lock()
        self._async_lock = asyncio.Lock()

    def wait(self) -> None:
        """Synchronous wait for next available slot."""
        with self._lock:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                time.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()

    async def async_wait(self) -> None:
        """Asynchronous wait for next available slot."""
        async with self._async_lock:
            now = time.time()
            elapsed = now - self.last_request_time
            if elapsed < self.min_interval:
                await asyncio.sleep(self.min_interval - elapsed)
            self.last_request_time = time.time()
