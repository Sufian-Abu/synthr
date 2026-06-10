"""Dual-key / origin enforcement (SPEC.md §2)."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_missing_key_is_invalid(client: TestClient, fillform_body: dict) -> None:
    r = client.post("/v1/fillForm", json=fillform_body)
    assert r.status_code == 401
    assert r.json()["error"]["code"] == "invalid_key"


def test_public_key_rejected_from_disallowed_origin(client: TestClient, fillform_body: dict) -> None:
    r = client.post(
        "/v1/fillForm",
        headers={"X-Project-Key": "pk_proj_test", "Origin": "https://evil.example"},
        json=fillform_body,
    )
    assert r.status_code == 403
    assert r.json()["error"]["code"] == "origin_not_allowed"


def test_public_key_allowed_from_allowed_origin(client: TestClient, fillform_body: dict) -> None:
    r = client.post(
        "/v1/fillForm",
        headers={"X-Project-Key": "pk_proj_test", "Origin": "http://localhost:3000"},
        json=fillform_body,
    )
    assert r.status_code == 200
