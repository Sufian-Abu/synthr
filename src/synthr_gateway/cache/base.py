"""Cache interface. Implementations: in-memory now, SQLite/embedding later."""

from __future__ import annotations

from typing import Protocol


class Cache(Protocol):
    def get(self, feature: str, payload: dict, ttl_minutes: int) -> dict | None: ...

    def set(self, feature: str, payload: dict, value: dict) -> None: ...
