"""image endpoint: envelope, image payload, and frontend_safe enforcement."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_image_returns_images(client: TestClient) -> None:
    r = client.post("/v1/image", headers=SECRET, json={"prompt": "a red shoe", "n": 2})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["feature"] == "image"
    assert len(body["data"]["images"]) == 2
    assert body["data"]["images"][0]["mime"] == "image/png"


def test_image_blocked_for_public_key(client: TestClient) -> None:
    # image has frontend_safe: false -> a public key may not call it
    r = client.post(
        "/v1/image",
        headers={"X-Project-Key": "pk_proj_test", "Origin": "http://localhost:3000"},
        json={"prompt": "a red shoe"},
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "feature_not_allowed"
