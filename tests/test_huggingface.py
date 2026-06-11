"""Hugging Face image adapter: image bytes -> base64, plus error mapping."""

from __future__ import annotations

import base64

import pytest

from synthr_gateway.core.errors import SynthrError
from synthr_gateway.providers import huggingface as hf


class _Resp:
    def __init__(self, status, headers, content=b"", json_body=None, text=""):
        self.status_code = status
        self.headers = headers
        self.content = content
        self._json = json_body
        self.text = text

    def json(self):
        if self._json is None:
            raise ValueError("no json")
        return self._json


class _Client:
    def __init__(self, resp):
        self._resp = resp

    async def __aenter__(self):
        return self

    async def __aexit__(self, *_):
        return False

    async def post(self, *_, **__):
        return self._resp


def _patch(monkeypatch, resp):
    monkeypatch.setattr(hf.httpx, "AsyncClient", lambda *a, **k: _Client(resp))


async def test_returns_image_b64(monkeypatch) -> None:
    _patch(monkeypatch, _Resp(200, {"content-type": "image/png"}, content=b"PNGBYTES"))
    r = await hf.HuggingFaceProvider("hf", api_key="hf_x").generate_image("a cat")
    assert r.images[0]["mime"] == "image/png"
    assert base64.b64decode(r.images[0]["b64"]) == b"PNGBYTES"


async def test_model_warmup_is_friendly(monkeypatch) -> None:
    _patch(monkeypatch, _Resp(503, {"content-type": "application/json"}, json_body={"error": "loading", "estimated_time": 20}))
    with pytest.raises(SynthrError) as exc:
        await hf.HuggingFaceProvider("hf", api_key="hf_x").generate_image("a cat")
    assert "warming up" in exc.value.message


async def test_bad_token(monkeypatch) -> None:
    _patch(monkeypatch, _Resp(401, {"content-type": "application/json"}, json_body={"error": "auth"}))
    with pytest.raises(SynthrError) as exc:
        await hf.HuggingFaceProvider("hf").generate_image("a cat")
    assert "HF_TOKEN" in exc.value.message
