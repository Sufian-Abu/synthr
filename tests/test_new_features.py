"""generate / rewrite / seo — new features run through the same pipeline."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_generate_returns_text(client: TestClient) -> None:
    r = client.post("/v1/generate", headers=SECRET, json={"prompt": "Write a tagline."})
    assert r.status_code == 200
    assert "text" in r.json()["data"]


def test_rewrite_returns_text(client: TestClient) -> None:
    r = client.post("/v1/rewrite", headers=SECRET, json={"text": "we was hoping", "instruction": "Fix grammar."})
    assert r.status_code == 200
    assert "text" in r.json()["data"]


def test_seo_returns_metadata_shape(client: TestClient) -> None:
    r = client.post("/v1/seo", headers=SECRET, json={"content": "A self-hosted AI gateway."})
    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"title", "description", "keywords"}
    assert isinstance(data["keywords"], list)


def test_generate_requires_auth(client: TestClient) -> None:
    r = client.post("/v1/generate", json={"prompt": "hi"})
    assert r.status_code == 401
