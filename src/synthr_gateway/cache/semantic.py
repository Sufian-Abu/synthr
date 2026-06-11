"""TF-IDF semantic cache. Opt-in per feature; correctness-first.

A query hits only if its TF-IDF cosine similarity to a stored prompt clears the feature's
threshold. Needs scikit-learn (the `semantic` extra); without it, it degrades to exact-text
match so requests still work — never serving a fuzzy hit it can't actually verify.
"""

from __future__ import annotations

import json
import time

from ..storage import Database


class SemanticCache:
    def __init__(self, db: Database) -> None:
        self.db = db
        try:
            import sklearn  # noqa: F401
            self.enabled = True
        except ImportError:
            self.enabled = False

    def _entries(self, feature: str, ttl_minutes: int) -> list:
        cutoff = time.time() - ttl_minutes * 60
        with self.db.lock:
            return self.db.conn.execute(
                "SELECT text, value FROM semantic_cache WHERE feature = ? AND created > ?",
                (feature, cutoff),
            ).fetchall()

    def _similarities(self, query: str, corpus: list[str]) -> list[float]:
        if not self.enabled:  # fallback: exact text match only
            return [1.0 if text == query else 0.0 for text in corpus]
        from sklearn.feature_extraction.text import TfidfVectorizer
        from sklearn.metrics.pairwise import cosine_similarity

        vectorizer = TfidfVectorizer().fit(corpus + [query])
        return cosine_similarity(vectorizer.transform([query]), vectorizer.transform(corpus))[0].tolist()

    def get(self, feature: str, text: str, ttl_minutes: int, threshold: float) -> dict | None:
        rows = self._entries(feature, ttl_minutes)
        if not rows:
            return None
        scores = self._similarities(text, [r["text"] for r in rows])
        best = max(range(len(scores)), key=scores.__getitem__)
        if scores[best] >= threshold:
            return json.loads(rows[best]["value"])
        return None

    def set(self, feature: str, text: str, value: dict) -> None:
        with self.db.lock:
            self.db.conn.execute(
                "INSERT INTO semantic_cache (feature, text, value, created) VALUES (?, ?, ?, ?)",
                (feature, text, json.dumps(value), time.time()),
            )
            self.db.conn.commit()
