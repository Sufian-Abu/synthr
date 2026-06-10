"""SQLite-backed exact-match cache (survives restarts)."""

from __future__ import annotations

import hashlib
import json
import time

from ..storage import Database


class SqliteExactCache:
    def __init__(self, db: Database) -> None:
        self.db = db

    @staticmethod
    def _key(feature: str, payload: dict) -> str:
        raw = feature + ":" + json.dumps(payload, sort_keys=True, default=str)
        return hashlib.sha256(raw.encode()).hexdigest()

    def get(self, feature: str, payload: dict, ttl_minutes: int) -> dict | None:
        key = self._key(feature, payload)
        with self.db.lock:
            row = self.db.conn.execute("SELECT value, created FROM cache WHERE key = ?", (key,)).fetchone()
            if row is None:
                return None
            if time.time() - row["created"] > ttl_minutes * 60:
                self.db.conn.execute("DELETE FROM cache WHERE key = ?", (key,))
                self.db.conn.commit()
                return None
        return json.loads(row["value"])

    def set(self, feature: str, payload: dict, value: dict) -> None:
        key = self._key(feature, payload)
        with self.db.lock:
            self.db.conn.execute(
                "INSERT OR REPLACE INTO cache (key, value, created) VALUES (?, ?, ?)",
                (key, json.dumps(value), time.time()),
            )
            self.db.conn.commit()
