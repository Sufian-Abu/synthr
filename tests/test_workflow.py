"""AI workflows: chain features, pipe outputs with ${N.key}, optional webhook (job)."""

from __future__ import annotations

import time

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_chains_steps_and_pipes_output(client: TestClient) -> None:
    r = client.post(
        "/v1/workflow",
        headers=SECRET,
        json={
            "steps": [
                {"feature": "summarize", "with": {"text": "hello world, this is a longer body of text"}},
                {"feature": "classify", "with": {"text": "${0.summary}", "labels": ["greeting", "other"]}},
            ]
        },
    )
    assert r.status_code == 200, r.text
    data = r.json()["data"]
    assert [s["feature"] for s in data["steps"]] == ["summarize", "classify"]
    assert set(data["result"]) == {"label", "confidence"}  # last step's output


def test_unknown_feature_is_422(client: TestClient) -> None:
    r = client.post("/v1/workflow", headers=SECRET, json={"steps": [{"feature": "nope", "with": {}}]})
    assert r.status_code == 422 and r.json()["error"]["code"] == "invalid_input"


def test_bad_reference_is_422(client: TestClient) -> None:
    r = client.post(
        "/v1/workflow",
        headers=SECRET,
        json={"steps": [{"feature": "summarize", "with": {"text": "${5.nope}"}}]},
    )
    assert r.status_code == 422


def test_requires_auth(client: TestClient) -> None:
    r = client.post("/v1/workflow", json={"steps": [{"feature": "summarize", "with": {"text": "hi"}}]})
    assert r.status_code == 401


def test_webhook_runs_as_job(client: TestClient) -> None:
    r = client.post(
        "/v1/workflow",
        headers=SECRET,
        json={
            "webhook": "http://127.0.0.1:9/none",  # unreachable; delivery is best-effort
            "steps": [{"feature": "summarize", "with": {"text": "hello world"}}],
        },
    )
    assert r.status_code == 200 and r.json()["status"] == "queued"
    job_id = r.json()["id"]
    for _ in range(80):
        g = client.get(f"/v1/jobs/{job_id}", headers=SECRET)
        if g.json()["status"] in ("done", "error"):
            break
        time.sleep(0.05)
    assert g.json()["status"] == "done"
    assert "result" in g.json()["result"]  # the workflow result dict {steps, result}
