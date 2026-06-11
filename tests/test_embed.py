"""embed — text(s) to vectors through the pipeline (mock provider)."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_embed_single_string(client: TestClient) -> None:
    r = client.post("/v1/embed", headers=SECRET, json={"input": "hello"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert data["dimensions"] == 3 and len(data["vectors"]) == 1


def test_embed_batch(client: TestClient) -> None:
    r = client.post("/v1/embed", headers=SECRET, json={"input": ["a", "bb", "ccc"]})
    assert r.status_code == 200
    vectors = r.json()["data"]["vectors"]
    assert len(vectors) == 3 and all(len(v) == 3 for v in vectors)
