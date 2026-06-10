"""Sliding-window rate limiting: per-user limit trips, other users unaffected."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from synthr_gateway.app import create_app

CONFIG = """
gateway:
  secret: test-secret
  db_path: ":memory:"
providers:
  mock: { kind: mock }
features:
  fillForm:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
projects:
  demo:
    keys:
      - { id: sk_proj_test, type: secret }
    limits:
      per_user: { daily_requests: 2 }
"""

BODY = {"fields": [{"name": "brand", "type": "string"}], "context": "Nike"}


@pytest.fixture()
def limited_client(tmp_path: Path) -> TestClient:
    cfg = tmp_path / "synthr.config.yaml"
    cfg.write_text(CONFIG)
    return TestClient(create_app(cfg))


def _post(client: TestClient, user: str) -> int:
    return client.post(
        "/v1/fillForm", headers={"X-Project-Key": "sk_proj_test", "X-User-Id": user}, json=BODY
    ).status_code


def test_user_hits_daily_limit(limited_client: TestClient) -> None:
    assert _post(limited_client, "u1") == 200
    assert _post(limited_client, "u1") == 200
    r = limited_client.post(
        "/v1/fillForm", headers={"X-Project-Key": "sk_proj_test", "X-User-Id": "u1"}, json=BODY
    )
    assert r.status_code == 429
    assert r.json()["error"]["code"] == "rate_limited"
    assert r.json()["error"]["retry_after_seconds"] > 0


def test_other_user_not_limited(limited_client: TestClient) -> None:
    _post(limited_client, "u1")
    _post(limited_client, "u1")
    assert _post(limited_client, "u2") == 200  # separate subject, own window
