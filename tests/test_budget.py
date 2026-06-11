"""Hard budget caps reject once a project is over its limit."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from synthr_gateway.app import create_app

CONFIG = """
gateway: { secret: t, db_path: ":memory:" }
providers:
  mock: { kind: mock }
features:
  summarize: { provider: mock, frontend_safe: true, cache: { enabled: false } }
  generate:  { provider: mock, frontend_safe: true, cache: { enabled: false } }
projects:
  demo:
    keys: [{ id: sk_proj_test, type: secret }]
    budget:
      daily_requests: 2
      per_feature_daily_requests: { generate: 1 }
"""

SECRET = {"X-Project-Key": "sk_proj_test"}


@pytest.fixture()
def budget_client(tmp_path: Path) -> TestClient:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CONFIG)
    return TestClient(create_app(cfg))


def test_daily_request_cap(budget_client: TestClient) -> None:
    body = {"text": "hello world"}
    assert budget_client.post("/v1/summarize", headers=SECRET, json=body).status_code == 200
    assert budget_client.post("/v1/summarize", headers=SECRET, json=body).status_code == 200
    r = budget_client.post("/v1/summarize", headers=SECRET, json=body)  # 3rd > cap of 2
    assert r.status_code == 402
    assert r.json()["error"]["code"] == "budget_exceeded"


def test_per_feature_daily_cap(budget_client: TestClient) -> None:
    assert budget_client.post("/v1/generate", headers=SECRET, json={"prompt": "hi"}).status_code == 200
    r = budget_client.post("/v1/generate", headers=SECRET, json={"prompt": "hi"})  # 2nd > feature cap of 1
    assert r.status_code == 402 and r.json()["error"]["code"] == "budget_exceeded"
