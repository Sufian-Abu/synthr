"""A tiny per-provider circuit breaker.

After `threshold` consecutive failover-eligible failures, a provider's circuit opens for
`cooldown` seconds — the runner then skips it and goes straight to the fallback instead of
hammering a provider that's down. A success closes it; after the cooldown one trial is
allowed (half-open).
"""

from __future__ import annotations

import threading
import time


class CircuitBreaker:
    def __init__(self, threshold: int = 5, cooldown: float = 30.0) -> None:
        self.threshold = threshold
        self.cooldown = cooldown
        self._fails: dict[str, int] = {}
        self._open_until: dict[str, float] = {}
        self._lock = threading.Lock()

    def is_open(self, name: str) -> bool:
        with self._lock:
            return self._open_until.get(name, 0.0) > time.monotonic()

    def record_success(self, name: str) -> None:
        with self._lock:
            self._fails.pop(name, None)
            self._open_until.pop(name, None)

    def record_failure(self, name: str) -> None:
        with self._lock:
            count = self._fails.get(name, 0) + 1
            self._fails[name] = count
            if count >= self.threshold:
                self._open_until[name] = time.monotonic() + self.cooldown

    def open_circuits(self) -> list[str]:
        now = time.monotonic()
        with self._lock:
            return [name for name, until in self._open_until.items() if until > now]

    def reset(self) -> None:
        with self._lock:
            self._fails.clear()
            self._open_until.clear()
