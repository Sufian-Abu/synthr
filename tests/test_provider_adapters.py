"""Per-provider adapter behaviour: JSON mode, error bodies, tool calls, streaming, image quirks."""

from __future__ import annotations

import json

import pytest

from synthr_gateway.core.errors import SynthrError
from synthr_gateway.providers import gemini as gm
from synthr_gateway.providers import openai_compat as oc
from synthr_gateway.providers.types import Message

SCHEMA = {"type": "object", "properties": {"a": {"type": "string"}}}


def _capture_post_json(monkeypatch, module, response: dict) -> dict:
    captured: dict = {}

    async def fake(url, *, json, headers=None, timeout=60.0, classify_error=None, **_):
        captured["url"] = url
        captured["json"] = json
        captured["classify"] = classify_error
        return response

    monkeypatch.setattr(module, "post_json", fake)
    return captured


# ── JSON mode differs per provider ─────────────────────────────────────────
async def test_openai_uses_strict_json_schema(monkeypatch) -> None:
    cap = _capture_post_json(monkeypatch, oc, {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})
    await oc.OpenAIProvider("openai", api_key="k").complete([Message("user", "hi")], model="gpt", json_schema=SCHEMA)
    rf = cap["json"]["response_format"]
    assert rf["type"] == "json_schema"
    assert rf["json_schema"]["schema"]["required"] == ["a"]
    assert rf["json_schema"]["schema"]["additionalProperties"] is False


async def test_groq_uses_json_object(monkeypatch) -> None:
    cap = _capture_post_json(monkeypatch, oc, {"choices": [{"message": {"content": "{}"}, "finish_reason": "stop"}]})
    await oc.GroqProvider("groq", api_key="k").complete([Message("user", "hi")], model="m", json_schema=SCHEMA)
    assert cap["json"]["response_format"] == {"type": "json_object"}


# ── error bodies map to typed codes ────────────────────────────────────────
def test_openai_error_rate_limit() -> None:
    err = oc._openai_error(429, json.dumps({"error": {"code": "rate_limit_exceeded", "message": "slow down"}}))
    assert err.code == "provider_rate_limited"


def test_openai_error_safety() -> None:
    err = oc._openai_error(400, json.dumps({"error": {"code": "content_policy_violation", "message": "no"}}))
    assert err.code == "provider_safety_blocked"


def test_ollama_error_freeform_body() -> None:
    err = oc._ollama_error(404, json.dumps({"error": "model 'llama9' not found"}))
    assert err.code == "provider_error" and "llama9" in err.message


def test_gemini_error_resource_exhausted() -> None:
    err = gm._gemini_error(429, json.dumps({"error": {"status": "RESOURCE_EXHAUSTED", "message": "quota"}}))
    assert err.code == "provider_rate_limited"


# ── content filter raises safety_blocked ───────────────────────────────────
async def test_finish_reason_content_filter_raises(monkeypatch) -> None:
    _capture_post_json(monkeypatch, oc, {"choices": [{"message": {"content": ""}, "finish_reason": "content_filter"}]})
    with pytest.raises(SynthrError) as exc:
        await oc.GroqProvider("groq", api_key="k").complete([Message("user", "hi")], model="m")
    assert exc.value.code == "provider_safety_blocked"


# ── tool calls parsed (OpenAI shape) ───────────────────────────────────────
async def test_tool_calls_parsed(monkeypatch) -> None:
    resp = {
        "choices": [
            {
                "message": {"content": None, "tool_calls": [{"id": "c1", "function": {"name": "lookup", "arguments": '{"q":1}'}}]},
                "finish_reason": "tool_calls",
            }
        ]
    }
    _capture_post_json(monkeypatch, oc, resp)
    result = await oc.OpenAIProvider("openai", api_key="k").complete([Message("user", "hi")], model="gpt")
    assert result.finish_reason == "tool_calls"
    assert result.tool_calls[0].name == "lookup" and result.tool_calls[0].arguments == '{"q":1}'


# ── Gemini maps tools to functionDeclarations and parses functionCall ───────
async def test_gemini_tools_roundtrip(monkeypatch) -> None:
    cap = _capture_post_json(
        monkeypatch,
        gm,
        {"candidates": [{"content": {"parts": [{"functionCall": {"name": "lookup", "args": {"q": 1}}}]}}]},
    )
    tools = [{"function": {"name": "lookup", "description": "x", "parameters": SCHEMA}}]
    result = await gm.GeminiProvider("gemini", api_key="k").complete([Message("user", "hi")], model="g", tools=tools)
    assert cap["json"]["tools"][0]["functionDeclarations"][0]["name"] == "lookup"
    assert result.tool_calls[0].name == "lookup" and json.loads(result.tool_calls[0].arguments) == {"q": 1}


# ── streaming yields text deltas ───────────────────────────────────────────
async def test_openai_streaming_yields_deltas(monkeypatch) -> None:
    async def fake_sse(url, *, json, headers=None, timeout=120.0, classify_error=None):
        for piece in ["Hel", "lo"]:
            yield {"choices": [{"delta": {"content": piece}}]}

    monkeypatch.setattr(oc, "post_sse", fake_sse)
    out = [c async for c in oc.OpenAIProvider("openai", api_key="k").stream_complete([Message("user", "hi")], model="gpt")]
    assert "".join(out) == "Hello"


# ── image API quirks ───────────────────────────────────────────────────────
async def test_grok_image_omits_size(monkeypatch) -> None:
    cap = _capture_post_json(monkeypatch, oc, {"data": [{"b64_json": "abc"}]})
    await oc.GrokProvider("grok", api_key="k").generate_image("a cat", size="1024x1024")
    assert "size" not in cap["json"]


async def test_openai_image_includes_size(monkeypatch) -> None:
    cap = _capture_post_json(monkeypatch, oc, {"data": [{"b64_json": "abc"}]})
    await oc.OpenAIProvider("openai", api_key="k").generate_image("a cat", size="512x512")
    assert cap["json"]["size"] == "512x512"


async def test_groq_has_no_image_capability() -> None:
    with pytest.raises(SynthrError):
        await oc.GroqProvider("groq", api_key="k").generate_image("a cat")
