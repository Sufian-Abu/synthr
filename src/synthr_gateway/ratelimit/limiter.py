"""Log-based sliding-window limiter.

Each accepted request inserts a timestamped row per policy scope; a limit is exceeded when
the count within the window reaches it. All policies are checked before any is consumed,
so a request never partially consumes quota.
"""

from __future__ import annotations

import time

from ..core import errors
from ..storage import Database
from .policy import Policy


class RateLimiter:
    def __init__(self, db: Database) -> None:
        self.db = db

    def enforce(self, policies: list[Policy]) -> None:
        if not policies:
            return
        now = time.time()
        with self.db.lock:
            for scope, limit, window in policies:
                since = now - window
                count = self.db.conn.execute(
                    "SELECT COUNT(*) FROM rate_events WHERE scope = ? AND ts > ?", (scope, since)
                ).fetchone()[0]
                if count >= limit:
                    oldest = self.db.conn.execute(
                        "SELECT MIN(ts) FROM rate_events WHERE scope = ? AND ts > ?", (scope, since)
                    ).fetchone()[0]
                    retry_after = int((oldest + window) - now) + 1 if oldest else int(window)
                    raise errors.rate_limited(retry_after)

            for scope, _limit, _window in policies:
                self.db.conn.execute("INSERT INTO rate_events (scope, ts) VALUES (?, ?)", (scope, now))
            self.db.conn.commit()
