"""Per-request usage logging + guardrail/limit events (powers the dashboard)."""

from __future__ import annotations

import time

from ..storage import Database
from .pricing import estimate_usd

_TOKENS = "COALESCE(SUM(prompt_tokens + completion_tokens), 0)"
_COST = "COALESCE(SUM(cost_usd), 0)"


class UsageLog:
    def __init__(self, db: Database) -> None:
        self.db = db

    # --- writes ---

    def record(
        self,
        *,
        project: str,
        subject: str,
        feature: str,
        provider: str,
        cached: bool,
        usage: dict,
        model: str | None = None,
    ) -> None:
        pt, ct = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
        cost = 0.0 if cached else estimate_usd(provider, model, pt, ct)
        with self.db.lock:
            self.db.conn.execute(
                "INSERT INTO usage (ts, project, subject, feature, provider, model, cached,"
                " prompt_tokens, completion_tokens, cost_usd) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (time.time(), project, subject, feature, provider, model, int(cached), pt, ct, cost),
            )
            self.db.conn.commit()

    def record_event(self, *, project: str, subject: str, kind: str, detail: str) -> None:
        with self.db.lock:
            self.db.conn.execute(
                "INSERT INTO events (ts, project, subject, kind, detail) VALUES (?, ?, ?, ?, ?)",
                (time.time(), project, subject, kind, detail),
            )
            self.db.conn.commit()

    # --- reads (dashboard) ---

    def totals(self) -> dict:
        with self.db.lock:
            row = self.db.conn.execute(
                f"SELECT COUNT(*) AS requests, COALESCE(SUM(cached),0) AS cache_hits,"
                f" {_TOKENS} AS tokens, {_COST} AS cost FROM usage"
            ).fetchone()
            blocked = self.db.conn.execute("SELECT COUNT(*) FROM events").fetchone()[0]
        requests, hits = row["requests"], row["cache_hits"]
        return {
            "requests": requests,
            "cache_hits": hits,
            "tokens": row["tokens"],
            "cost": row["cost"],
            "blocked": blocked,
            "cache_hit_rate": round(100 * hits / requests) if requests else 0,
        }

    def by_feature(self) -> list[dict]:
        with self.db.lock:
            rows = self.db.conn.execute(
                f"SELECT feature, COUNT(*) AS n, COALESCE(SUM(cached),0) AS hits, {_TOKENS} AS tokens"
                " FROM usage GROUP BY feature ORDER BY n DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def by_provider(self) -> list[dict]:
        with self.db.lock:
            rows = self.db.conn.execute(
                f"SELECT provider, COUNT(*) AS n, {_TOKENS} AS tokens, {_COST} AS cost"
                " FROM usage GROUP BY provider ORDER BY n DESC"
            ).fetchall()
        return [dict(r) for r in rows]

    def recent(self, limit: int = 15) -> list[dict]:
        with self.db.lock:
            rows = self.db.conn.execute(
                "SELECT ts, subject, feature, provider, cached, prompt_tokens, completion_tokens, cost_usd"
                " FROM usage ORDER BY id DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {
                "time": time.strftime("%H:%M:%S", time.localtime(r["ts"])),
                "subject": r["subject"],
                "feature": r["feature"],
                "provider": r["provider"],
                "cached": bool(r["cached"]),
                "tokens": (r["prompt_tokens"] or 0) + (r["completion_tokens"] or 0),
                "cost": r["cost_usd"] or 0,
            }
            for r in rows
        ]

    def recent_events(self, limit: int = 10) -> list[dict]:
        with self.db.lock:
            rows = self.db.conn.execute(
                "SELECT ts, subject, kind, detail FROM events ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
        return [
            {
                "time": time.strftime("%H:%M:%S", time.localtime(r["ts"])),
                "subject": r["subject"],
                "kind": r["kind"],
                "detail": r["detail"],
            }
            for r in rows
        ]
