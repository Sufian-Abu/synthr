"""summarize + translate endpoints (mock provider echoes the prompt)."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_summarize_shape(client: TestClient) -> None:
    r = client.post("/v1/summarize", headers=SECRET, json={"text": "a long article", "max_words": 20})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["feature"] == "summarize"
    assert "summary" in body["data"]


def test_translate_shape(client: TestClient) -> None:
    r = client.post("/v1/translate", headers=SECRET, json={"text": "hello", "target_lang": "Spanish"})
    assert r.status_code == 200
    assert "translation" in r.json()["data"]


def test_summarize_validates_empty_text(client: TestClient) -> None:
    r = client.post("/v1/summarize", headers=SECRET, json={"text": ""})
    assert r.status_code == 422
