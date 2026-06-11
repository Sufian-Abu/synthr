"""Background jobs: submit a feature, poll until done; auth-scoped reads."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def _poll(client: TestClient, job_id: str, headers: dict, tries: int = 80) -> dict:
    for _ in range(tries):
        r = client.get(f"/v1/jobs/{job_id}", headers=headers)
        assert r.status_code == 200, r.text
        body = r.json()
        if body["status"] in ("done", "error"):
            return body
        time.sleep(0.05)
    raise AssertionError("job did not finish in time")


def test_submit_and_complete(client: TestClient) -> None:
    r = client.post("/v1/jobs", headers=SECRET, json={"feature": "summarize", "payload": {"text": "hello world"}})
    assert r.status_code == 200
    assert r.json()["status"] == "queued"
    job = _poll(client, r.json()["id"], SECRET)
    assert job["status"] == "done"
    assert "summary" in job["result"]


def test_unknown_feature_rejected(client: TestClient) -> None:
    r = client.post("/v1/jobs", headers=SECRET, json={"feature": "nope", "payload": {}})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_input"


def test_missing_job_is_404(client: TestClient) -> None:
    r = client.get("/v1/jobs/job_doesnotexist", headers=SECRET)
    assert r.status_code == 404 and r.json()["error"]["code"] == "not_found"


def test_job_requires_auth(client: TestClient) -> None:
    r = client.post("/v1/jobs", json={"feature": "summarize", "payload": {"text": "hi"}})
    assert r.status_code == 401
