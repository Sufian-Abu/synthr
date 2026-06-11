"""OpenAI-compatible /v1/chat/completions: shape, bearer auth, errors, streaming."""

from __future__ import annotations

from fastapi.testclient import TestClient

BODY = {"model": "mock-model", "messages": [{"role": "user", "content": "hello there"}]}


def test_chat_completion_openai_shape(client: TestClient) -> None:
    r = client.post("/v1/chat/completions", headers={"Authorization": "Bearer sk_proj_test"}, json=BODY)
    assert r.status_code == 200
    body = r.json()
    assert body["object"] == "chat.completion"
    assert body["model"] == "mock-model"
    assert body["choices"][0]["message"]["role"] == "assistant"
    assert body["choices"][0]["message"]["content"] == "hello there"  # mock echoes last user message
    assert body["choices"][0]["finish_reason"] == "stop"
    assert "total_tokens" in body["usage"]


def test_chat_accepts_x_project_key_too(client: TestClient) -> None:
    r = client.post("/v1/chat/completions", headers={"X-Project-Key": "sk_proj_test"}, json=BODY)
    assert r.status_code == 200


def test_chat_invalid_key_returns_openai_error(client: TestClient) -> None:
    r = client.post("/v1/chat/completions", headers={"Authorization": "Bearer nope"}, json=BODY)
    assert r.status_code == 401
    err = r.json()["error"]
    assert err["type"] == "invalid_key" and err["message"]


def test_chat_provider_error_in_openai_shape(client: TestClient, monkeypatch) -> None:
    from synthr_gateway.core import errors

    async def boom(*_, **__):
        raise errors.provider_error("upstream down")

    monkeypatch.setattr(client.app.state.providers["mock"], "complete", boom)
    r = client.post("/v1/chat/completions", headers={"Authorization": "Bearer sk_proj_test"}, json=BODY)
    assert r.status_code == 502
    assert r.json()["error"]["type"] == "provider_error"


def test_chat_streaming_sse(client: TestClient) -> None:
    r = client.post(
        "/v1/chat/completions",
        headers={"Authorization": "Bearer sk_proj_test"},
        json={**BODY, "stream": True},
    )
    assert r.status_code == 200
    assert r.headers["content-type"].startswith("text/event-stream")
    text = r.text
    assert "chat.completion.chunk" in text
    assert "hello there" in text  # the content delta
    assert "data: [DONE]" in text
