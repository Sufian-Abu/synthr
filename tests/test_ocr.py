"""ocr — image → text via the vision capability (mock provider)."""

from __future__ import annotations

import base64

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}
_PNG = base64.b64encode(b"fake-png-bytes").decode()


def test_ocr_from_base64(client: TestClient) -> None:
    r = client.post("/v1/ocr", headers=SECRET, json={"image": _PNG})
    assert r.status_code == 200
    assert "text" in r.json()["data"]


def test_ocr_from_data_uri(client: TestClient) -> None:
    r = client.post("/v1/ocr", headers=SECRET, json={"image": f"data:image/png;base64,{_PNG}"})
    assert r.status_code == 200


def test_ocr_requires_an_image(client: TestClient) -> None:
    r = client.post("/v1/ocr", headers=SECRET, json={})
    assert r.status_code == 422


def test_ocr_requires_auth(client: TestClient) -> None:
    r = client.post("/v1/ocr", json={"image": _PNG})
    assert r.status_code == 401
