"""Usage logging: each served request writes one row (incl. cache hits)."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_request_is_logged(client: TestClient) -> None:
    body = {"fields": [{"name": "brand", "type": "string"}], "context": "Nike"}
    client.post("/v1/fillForm", headers=SECRET, json=body)
    client.post("/v1/fillForm", headers=SECRET, json=body)  # cache hit

    rows = client.app.state.db.conn.execute(
        "SELECT feature, provider, cached FROM usage ORDER BY id"
    ).fetchall()
    assert len(rows) == 2
    assert rows[0]["feature"] == "fillForm"
    assert rows[0]["provider"] == "mock"
    assert rows[0]["cached"] == 0
    assert rows[1]["cached"] == 1  # second call served from cache, still logged
