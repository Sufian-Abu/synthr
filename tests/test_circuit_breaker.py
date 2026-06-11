"""Circuit breaker: a repeatedly-failing provider gets skipped (straight to fallback)."""

from __future__ import annotations

from pathlib import Path

from fastapi.testclient import TestClient

from synthr_gateway.api import runner
from synthr_gateway.app import create_app
from synthr_gateway.core import errors

CONFIG = """
gateway: { secret: t, db_path: ":memory:" }
providers:
  flaky:  { kind: mock }
  backup: { kind: mock }
features:
  summarize:
    provider: flaky
    fallback: { provider: backup }
    frontend_safe: true
    cache: { enabled: false }
projects:
  demo:
    keys: [{ id: sk_proj_test, type: secret }]
"""

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_circuit_opens_and_skips_dead_provider(tmp_path: Path, monkeypatch) -> None:
    runner.circuit_breaker.reset()  # module-global — isolate this test
    cfg = tmp_path / "c.yaml"
    cfg.write_text(CONFIG)
    app = create_app(cfg)

    calls = {"n": 0}

    async def boom(*_, **__):
        calls["n"] += 1
        raise errors.provider_error("flaky is down")

    monkeypatch.setattr(app.state.providers["flaky"], "complete", boom)
    client = TestClient(app)
    body = {"text": "hello world"}

    # threshold=5: each of the first 5 calls hits flaky (fails) then fails over to backup
    for _ in range(runner.circuit_breaker.threshold):
        assert client.post("/v1/summarize", headers=SECRET, json=body).status_code == 200
    assert calls["n"] == runner.circuit_breaker.threshold
    assert "flaky" in runner.circuit_breaker.open_circuits()

    # circuit now open — flaky is skipped entirely, backup still serves
    assert client.post("/v1/summarize", headers=SECRET, json=body).status_code == 200
    assert calls["n"] == runner.circuit_breaker.threshold  # flaky.complete was NOT called again

    runner.circuit_breaker.reset()
