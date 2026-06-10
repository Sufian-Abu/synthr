"""In-memory exact-match cache (SPEC.md §5).

Exact mode only: key = hash of (feature + normalized input). Zero false hits.
Similarity/embedding caching is a deliberate Phase-2 add and stays opt-in per feature.
"""

from __future__ import annotations

import hashlib
import json
import time


class InMemoryExactCache:
    def __init__(self) -> None:
        self._store: dict[str, tuple[dict, float]] = {}

    @staticmethod
    def _key(feature: str, payload: dict) -> str:
        raw = feature + ":" + json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, feature: str, payload: dict, ttl_minutes: int) -> dict | None:
        key = self._key(feature, payload)
        entry = self._store.get(key)
        if entry is None:
            return None
        value, created = entry
        if time.time() - created > ttl_minutes * 60:
            self._store.pop(key, None)
            return None
        return value

    def set(self, feature: str, payload: dict, value: dict) -> None:
        self._store[self._key(feature, payload)] = (value, time.time())
