"""Response cache. Exact-match (default) + opt-in TF-IDF semantic, routed by CacheManager."""

from .base import Cache
from .manager import CacheManager
from .memory import InMemoryExactCache
from .semantic import SemanticCache
from .sqlite import SqliteExactCache

__all__ = ["Cache", "CacheManager", "InMemoryExactCache", "SemanticCache", "SqliteExactCache"]
