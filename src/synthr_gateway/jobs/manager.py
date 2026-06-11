"""Runs jobs off the request thread.

Each job runs in a thread-pool worker with its own event loop (`asyncio.run`), so slow
features (image generation, background removal) never block the gateway's main loop. This
is the MVP background-worker; a real queue (arq/Celery) is on the roadmap.
"""

from __future__ import annotations

import asyncio
from collections.abc import Callable, Coroutine
from concurrent.futures import ThreadPoolExecutor
from typing import Any

from ..core import errors
from .store import JobStore

JobCoro = Callable[[], Coroutine[Any, Any, dict]]


class JobManager:
    def __init__(self, store: JobStore, workers: int = 4) -> None:
        self.store = store
        self.pool = ThreadPoolExecutor(max_workers=workers, thread_name_prefix="synthr-job")

    def submit(self, job_id: str, run: JobCoro) -> None:
        """Schedule `run()` (an async factory returning the result data) on a worker."""
        self.pool.submit(self._run, job_id, run)

    def _run(self, job_id: str, run: JobCoro) -> None:
        self.store.set_running(job_id)
        try:
            data: dict = asyncio.run(run())
            self.store.set_done(job_id, data)
        except errors.SynthrError as exc:
            self.store.set_error(job_id, exc.code, exc.message)
        except Exception as exc:  # noqa: BLE001 — any failure becomes a job error, not a crash
            self.store.set_error(job_id, "internal_error", str(exc))
