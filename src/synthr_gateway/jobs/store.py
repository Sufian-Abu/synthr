"""SQLite-backed job store for async features (image, background removal, ...)."""

from __future__ import annotations

import json
import time

from ..storage import Database


class JobStore:
    def __init__(self, db: Database) -> None:
        self.db = db

    def create(self, job_id: str, *, project: str, subject: str, feature: str) -> None:
        now = time.time()
        with self.db.lock:
            self.db.conn.execute(
                "INSERT INTO jobs (id, ts, updated, project, subject, feature, status) "
                "VALUES (?, ?, ?, ?, ?, ?, 'queued')",
                (job_id, now, now, project, subject, feature),
            )
            self.db.conn.commit()

    def _set(self, job_id: str, **fields: object) -> None:
        fields["updated"] = time.time()
        cols = ", ".join(f"{k} = ?" for k in fields)
        with self.db.lock:
            self.db.conn.execute(f"UPDATE jobs SET {cols} WHERE id = ?", (*fields.values(), job_id))
            self.db.conn.commit()

    def set_running(self, job_id: str) -> None:
        self._set(job_id, status="running")

    def set_done(self, job_id: str, result: dict) -> None:
        self._set(job_id, status="done", result=json.dumps(result))

    def set_error(self, job_id: str, code: str, message: str) -> None:
        self._set(job_id, status="error", error_code=code, error_msg=message)

    def get(self, job_id: str) -> dict | None:
        with self.db.lock:
            row = self.db.conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if row is None:
            return None
        out: dict = {
            "id": row["id"],
            "feature": row["feature"],
            "status": row["status"],
            "project": row["project"],
            "created": row["ts"],
            "updated": row["updated"],
        }
        if row["result"]:
            out["result"] = json.loads(row["result"])
        if row["error_code"]:
            out["error"] = {"code": row["error_code"], "message": row["error_msg"]}
        return out
