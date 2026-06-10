"""fillForm endpoint: envelope shape, schema-keyed output, health."""

from __future__ import annotations

from fastapi.testclient import TestClient

KEY = {"X-Project-Key": "sk_proj_test"}


def test_health(client: TestClient) -> None:
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_returns_envelope_with_schema_keys(client: TestClient, fillform_body: dict) -> None:
    r = client.post("/v1/fillForm", headers=KEY, json=fillform_body)
    assert r.status_code == 200
    body = r.json()
    assert body["meta"]["feature"] == "fillForm"
    assert body["meta"]["provider"] == "mock"
    assert body["meta"]["cached"] is False
    # mock returns nulls -> every requested field present, all unfilled
    assert set(body["data"]["values"]) == {"brand", "size", "color"}
    assert set(body["data"]["unfilled"]) == {"brand", "size", "color"}
