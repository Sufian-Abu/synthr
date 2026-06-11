"""Provider fallback: primary provider_error -> fallback serves the request."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from synthr_gateway.app import create_app
from synthr_gateway.core import errors

CONFIG = """
gateway: { secret: t, db_path: ":memory:" }
providers:
  primary: { kind: mock }
  backup:  { kind: mock }
features:
  summarize:
    provider: primary
    fallback: { provider: backup }
    frontend_safe: true
    cache: { enabled: false }
projects:
  demo:
    keys: [{ id: sk_proj_test, type: secret }]
"""

SECRET = {"X-Project-Key": "sk_proj_test"}


@pytest.fixture()
def fb_app(tmp_path: Path):
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CONFIG)
    return create_app(cfg)


def test_falls_back_when_primary_errors(fb_app, monkeypatch) -> None:
    async def boom(*_, **__):
        raise errors.provider_error("primary is down")

    monkeypatch.setattr(fb_app.state.providers["primary"], "complete", boom)
    client = TestClient(fb_app)

    r = client.post("/v1/summarize", headers=SECRET, json={"text": "hello world"})
    assert r.status_code == 200
    assert r.json()["meta"]["provider"] == "backup"  # served by the fallback


def test_primary_serves_when_healthy(fb_app) -> None:
    r = TestClient(fb_app).post("/v1/summarize", headers=SECRET, json={"text": "hello world"})
    assert r.status_code == 200
    assert r.json()["meta"]["provider"] == "primary"


@pytest.mark.parametrize(
    "make_error",
    [errors.provider_timeout, errors.provider_rate_limited, errors.provider_invalid_response],
)
def test_fails_over_on_recoverable_errors(fb_app, monkeypatch, make_error) -> None:
    async def boom(*_, **__):
        raise make_error()

    monkeypatch.setattr(fb_app.state.providers["primary"], "complete", boom)
    r = TestClient(fb_app).post("/v1/summarize", headers=SECRET, json={"text": "hello world"})
    assert r.status_code == 200
    assert r.json()["meta"]["provider"] == "backup"


def test_does_not_fail_over_on_safety_block(fb_app, monkeypatch) -> None:
    async def boom(*_, **__):
        raise errors.provider_safety_blocked()

    monkeypatch.setattr(fb_app.state.providers["primary"], "complete", boom)
    r = TestClient(fb_app).post("/v1/summarize", headers=SECRET, json={"text": "hello world"})
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "provider_safety_blocked"
