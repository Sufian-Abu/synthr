"""Output guardrails: PII in a response is redacted (mock echoes the prompt)."""

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
  summarize:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
    guardrails: { redact_output_pii: true }
projects:
  demo:
    keys: [{ id: sk_proj_test, type: secret }]
"""

SECRET = {"X-Project-Key": "sk_proj_test"}


@pytest.fixture()
def oclient(tmp_path: Path) -> TestClient:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CONFIG)
    return TestClient(create_app(cfg))


def test_email_redacted_from_output(oclient: TestClient) -> None:
    # mock echoes the prompt, so the email appears in the output and must be scrubbed
    r = oclient.post("/v1/summarize", headers=SECRET, json={"text": "reach me at john@example.com anytime"})
    assert r.status_code == 200
    summary = r.json()["data"]["summary"]
    assert "john@example.com" not in summary
    assert "[redacted-email]" in summary


def test_redaction_logs_event(oclient: TestClient) -> None:
    oclient.post("/v1/summarize", headers=SECRET, json={"text": "card 4111 1111 1111 1111"})
    rows = oclient.app.state.db.conn.execute("SELECT kind FROM events").fetchall()
    assert any(r["kind"] == "output_redacted" for r in rows)
