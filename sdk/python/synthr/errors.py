"""Error raised when the gateway returns an error envelope."""

from __future__ import annotations


class SynthrError(Exception):
    def __init__(self, code: str, message: str, status: int, retry_after: int | None = None) -> None:
        super().__init__(f"{code}: {message}")
        self.code = code
        self.message = message
        self.status = status
        self.retry_after = retry_after
