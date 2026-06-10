"""Routes each request to the right cache by the feature's configured mode."""

from __future__ import annotations

from ..config.schema import CacheCfg
from ..storage import Database
from .semantic import SemanticCache
from .sqlite import SqliteExactCache


class CacheManager:
    def __init__(self, db: Database) -> None:
        self._exact = SqliteExactCache(db)
        self._semantic = SemanticCache(db)

    def get(self, feature: str, cfg: CacheCfg, payload: dict, text: str | None) -> dict | None:
        if not cfg.enabled:
            return None
        if cfg.mode == "similar" and text:
            return self._semantic.get(feature, text, cfg.ttl_minutes, cfg.similarity_threshold)
        return self._exact.get(feature, payload, cfg.ttl_minutes)

    def set(self, feature: str, cfg: CacheCfg, payload: dict, value: dict, text: str | None) -> None:
        if not cfg.enabled:
            return
        if cfg.mode == "similar" and text:
            self._semantic.set(feature, text, value)
        else:
            self._exact.set(feature, payload, value)
