"""SDK unit tests using httpx.MockTransport — no gateway/server needed."""

from __future__ import annotations

import json

import httpx
import pytest

from synthr import AI, AsyncAI, SynthrError


def _ok(handler_capture: dict):
    def handler(request: httpx.Request) -> httpx.Response:
        handler_capture["path"] = request.url.path
        handler_capture["key"] = request.headers.get("x-project-key")
        handler_capture["body"] = json.loads(request.content)
        return httpx.Response(200, json={"data": {"echo": True}, "meta": {"feature": "x"}})

    return handler


def test_fill_form_builds_request_and_unwraps() -> None:
    cap: dict = {}
    client = httpx.Client(transport=httpx.MockTransport(_ok(cap)), base_url="http://test")
    ai = AI(key="sk_test", http_client=client)

    data = ai.fill_form(fields=[{"name": "brand", "type": "string"}], context="Nike")

    assert data == {"echo": True}
    assert cap["path"] == "/v1/fillForm"
    assert cap["key"] == "sk_test"
    assert cap["body"]["context"] == "Nike"


def test_error_envelope_raises() -> None:
    def handler(_: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"error": {"code": "rate_limited", "message": "slow down", "retry_after_seconds": 60}})

    client = httpx.Client(transport=httpx.MockTransport(handler), base_url="http://test")
    ai = AI(key="sk_test", http_client=client)

    with pytest.raises(SynthrError) as exc:
        ai.summarize(text="hi")
    assert exc.value.code == "rate_limited"
    assert exc.value.retry_after == 60


async def test_async_translate() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(200, json={"data": {"translation": body["target_lang"]}, "meta": {}})

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler), base_url="http://test")
    ai = AsyncAI(key="sk_test", http_client=client)
    data = await ai.translate(text="hi", target_lang="Spanish")
    assert data["translation"] == "Spanish"
