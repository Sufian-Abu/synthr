"""Input guardrails: PII, length, and keyword blocks (before any provider call)."""

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
  fillForm:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
    guardrails:
      block_pii: true
      max_prompt_length: 200
      blocked_keywords: ["topsecret"]
projects:
  demo:
    keys: [{ id: sk_proj_test, type: secret }]
"""

SECRET = {"X-Project-Key": "sk_proj_test"}


@pytest.fixture()
def gclient(tmp_path: Path) -> TestClient:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CONFIG)
    return TestClient(create_app(cfg))


def _post(client: TestClient, context: str):
    return client.post(
        "/v1/fillForm",
        headers=SECRET,
        json={"fields": [{"name": "x", "type": "string"}], "context": context},
    )


def test_credit_card_blocked(gclient: TestClient) -> None:
    r = _post(gclient, "my card is 4111 1111 1111 1111 please")
    assert r.status_code == 400
    assert r.json()["error"]["code"] == "guardrail_blocked"


def test_clean_input_passes(gclient: TestClient) -> None:
    assert _post(gclient, "Nike Air Max size 10").status_code == 200


def test_blocked_keyword(gclient: TestClient) -> None:
    assert _post(gclient, "this is topsecret info").status_code == 400


def test_too_long_blocked(gclient: TestClient) -> None:
    assert _post(gclient, "x" * 500).status_code == 400


def test_block_is_logged_as_event(gclient: TestClient) -> None:
    _post(gclient, "card 4111 1111 1111 1111")
    rows = gclient.app.state.db.conn.execute("SELECT kind FROM events").fetchall()
    assert any(r["kind"] == "guardrail_blocked" for r in rows)
