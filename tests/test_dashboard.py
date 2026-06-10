"""Dashboard renders and reflects logged usage."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_dashboard_page_renders(client: TestClient) -> None:
    r = client.get("/dashboard")
    assert r.status_code == 200
    assert "usage dashboard" in r.text


def test_stats_partial_reflects_requests(client: TestClient) -> None:
    client.post("/v1/summarize", headers=SECRET, json={"text": "hello world"})
    r = client.get("/dashboard/stats")
    assert r.status_code == 200
    assert "summarize" in r.text  # the feature shows up in the table
