"""removeBackground endpoint: base64 in -> base64 PNG out, plus input validation."""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}
SAMPLE_B64 = base64.b64encode(b"fake-image-bytes").decode()


def test_removebg_returns_png_b64(client: TestClient) -> None:
    r = client.post("/v1/removeBackground", headers=SECRET, json={"image": SAMPLE_B64})
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["feature"] == "removeBackground"
    assert body["data"]["image"]["mime"] == "image/png"
    # mock echoes the bytes, so round-trip matches the input
    assert body["data"]["image"]["b64"] == SAMPLE_B64


def test_removebg_requires_an_image(client: TestClient) -> None:
    r = client.post("/v1/removeBackground", headers=SECRET, json={})
    assert r.status_code == 422  # pydantic validation: need image or image_url
