"""Single SQLite connection shared across the gateway.

One connection (check_same_thread=False) guarded by a lock — simple and correct at our
scale, and works with both file paths and ":memory:". Schema is created on open, and a
tiny migration adds newer columns to pre-existing databases.
"""

from __future__ import annotations

import sqlite3
import threading

SCHEMA = """
CREATE TABLE IF NOT EXISTS cache (
    key     TEXT PRIMARY KEY,
    value   TEXT NOT NULL,
    created REAL NOT NULL
);
CREATE TABLE IF NOT EXISTS usage (
    id                INTEGER PRIMARY KEY AUTOINCREMENT,
    ts                REAL NOT NULL,
    project           TEXT,
    subject           TEXT,
    feature           TEXT,
    provider          TEXT,
    model             TEXT,
    cached            INTEGER,
    prompt_tokens     INTEGER,
    completion_tokens INTEGER,
    cost_usd          REAL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS events (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    ts      REAL NOT NULL,
    project TEXT,
    subject TEXT,
    kind    TEXT,
    detail  TEXT
);
CREATE TABLE IF NOT EXISTS semantic_cache (
    id      INTEGER PRIMARY KEY AUTOINCREMENT,
    feature TEXT NOT NULL,
    text    TEXT NOT NULL,
    value   TEXT NOT NULL,
    created REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_sem_feature ON semantic_cache(feature);
CREATE TABLE IF NOT EXISTS rate_events (
    id    INTEGER PRIMARY KEY AUTOINCREMENT,
    scope TEXT NOT NULL,
    ts    REAL NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_rate_scope_ts ON rate_events(scope, ts);
CREATE INDEX IF NOT EXISTS idx_usage_ts ON usage(ts);
CREATE INDEX IF NOT EXISTS idx_events_ts ON events(ts);
CREATE TABLE IF NOT EXISTS jobs (
    id         TEXT PRIMARY KEY,
    ts         REAL NOT NULL,
    updated    REAL NOT NULL,
    project    TEXT,
    subject    TEXT,
    feature    TEXT,
    status     TEXT NOT NULL,
    result     TEXT,
    error_code TEXT,
    error_msg  TEXT
);
"""

# Columns added after v1 — applied to pre-existing usage tables.
_USAGE_MIGRATIONS = {"model": "TEXT", "cost_usd": "REAL DEFAULT 0"}


class Database:
    def __init__(self, path: str) -> None:
        self.conn = sqlite3.connect(path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.lock = threading.Lock()
        with self.lock:
            self.conn.executescript(SCHEMA)
            self._migrate()
            self.conn.commit()

    def _migrate(self) -> None:
        existing = {row["name"] for row in self.conn.execute("PRAGMA table_info(usage)")}
        for column, decl in _USAGE_MIGRATIONS.items():
            if column not in existing:
                self.conn.execute(f"ALTER TABLE usage ADD COLUMN {column} {decl}")
