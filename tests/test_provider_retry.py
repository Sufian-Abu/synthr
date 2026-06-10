"""post_json retry behaviour — transient 5xx are retried, then succeed or raise a typed error."""

from __future__ import annotations

import pytest

from synthr_gateway.core.errors import SynthrError
from synthr_gateway.providers import http as http_mod


class _Resp:
    def __init__(self, status: int) -> None:
        self.status_code = status
        self.headers: dict = {}
        self.text = ""

    def json(self) -> dict:
        return {"ok": True}


class _Client:
    def __init__(self, seq) -> None:
        self._seq = seq

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_) -> bool:
        return False

    async def post(self, *_, **__) -> _Resp:
        return _Resp(next(self._seq))


@pytest.fixture(autouse=True)
def _no_sleep(monkeypatch):
    async def nosleep(*_, **__):
        return None

    monkeypatch.setattr(http_mod.asyncio, "sleep", nosleep)


def _patch_statuses(monkeypatch, statuses: list[int]) -> None:
    seq = iter(statuses)
    monkeypatch.setattr(http_mod.httpx, "AsyncClient", lambda *a, **k: _Client(seq))


async def test_retries_then_succeeds(monkeypatch) -> None:
    _patch_statuses(monkeypatch, [503, 503, 200])
    assert await http_mod.post_json("http://x", json={}) == {"ok": True}


async def test_raises_after_exhausting_retries(monkeypatch) -> None:
    _patch_statuses(monkeypatch, [503, 503, 503])
    with pytest.raises(SynthrError) as exc:
        await http_mod.post_json("http://x", json={})
    assert exc.value.code == "provider_error"


async def test_non_retryable_4xx_raises_immediately(monkeypatch) -> None:
    _patch_statuses(monkeypatch, [400, 200, 200])  # 2nd/3rd never reached
    with pytest.raises(SynthrError) as exc:
        await http_mod.post_json("http://x", json={})
    assert exc.value.code == "provider_error"


async def test_429_maps_to_provider_rate_limited(monkeypatch) -> None:
    _patch_statuses(monkeypatch, [429, 429, 429])
    with pytest.raises(SynthrError) as exc:
        await http_mod.post_json("http://x", json={})
    assert exc.value.code == "provider_rate_limited"
