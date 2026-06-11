"""CORS: browsers can use public keys from a declared origin, and only those."""

from __future__ import annotations

from fastapi.testclient import TestClient


def test_preflight_allows_declared_origin(client: TestClient) -> None:
    r = client.options(
        "/v1/fillForm",
        headers={"Origin": "http://localhost:3000", "Access-Control-Request-Method": "POST"},
    )
    assert r.status_code == 200
    assert r.headers.get("access-control-allow-origin") == "http://localhost:3000"


def test_disallowed_origin_gets_no_cors_header(client: TestClient) -> None:
    r = client.options(
        "/v1/fillForm",
        headers={"Origin": "https://evil.example", "Access-Control-Request-Method": "POST"},
    )
    assert r.headers.get("access-control-allow-origin") is None
