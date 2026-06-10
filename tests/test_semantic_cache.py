"""Semantic (TF-IDF) cache: a near-duplicate prompt hits; an unrelated one misses.

Requires the `semantic` extra (scikit-learn); skipped if not installed.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from synthr_gateway.app import create_app

pytest.importorskip("sklearn")

CONFIG = """
gateway: { secret: t, db_path: ":memory:" }
providers:
  mock: { kind: mock }
features:
  summarize:
    provider: mock
    frontend_safe: true
    cache: { enabled: true, mode: similar, ttl_minutes: 60, similarity_threshold: 0.5 }
projects:
  demo:
    keys: [{ id: sk_proj_test, type: secret }]
"""

SECRET = {"X-Project-Key": "sk_proj_test"}


@pytest.fixture()
def sclient(tmp_path: Path) -> TestClient:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CONFIG)
    return TestClient(create_app(cfg))


def _summarize(client: TestClient, text: str) -> bool:
    r = client.post("/v1/summarize", headers=SECRET, json={"text": text})
    assert r.status_code == 200
    return r.json()["meta"]["cached"]


def test_near_duplicate_hits(sclient: TestClient) -> None:
    assert _summarize(sclient, "please summarize the quarterly sales report") is False
    # same words, reordered -> high TF-IDF cosine similarity -> cache hit
    assert _summarize(sclient, "summarize the quarterly sales report please") is True


def test_unrelated_prompt_misses(sclient: TestClient) -> None:
    _summarize(sclient, "please summarize the quarterly sales report")
    assert _summarize(sclient, "explain how photosynthesis works in plants") is False
