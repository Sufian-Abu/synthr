"""SQLite-backed persistence shared by cache, usage logging, and rate limiting."""

from .db import Database

__all__ = ["Database"]
