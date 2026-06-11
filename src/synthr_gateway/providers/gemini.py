"""Native Gemini adapter (generativelanguage REST API).

Gemini differs from OpenAI on every axis this gateway cares about: system goes in
`systemInstruction`; structured output is `responseMimeType` + `responseSchema`; tools are
`functionDeclarations` and come back as `functionCall` parts; streaming is
`:streamGenerateContent?alt=sse`; and errors use Google's `{error:{status,message}}` shape.
"""

from __future__ import annotations

import json as jsonlib
from collections.abc import AsyncIterator

from ..core import errors
from .base import Provider
from .http import post_json, post_sse
from .types import Capability, CompletionResult, EmbedResult, ImageResult, Message, ToolCall

_TYPE_MAP = {
    "string": "STRING",
    "number": "NUMBER",
    "integer": "INTEGER",
    "boolean": "BOOLEAN",
    "object": "OBJECT",
    "array": "ARRAY",
}


def to_gemini_schema(schema: dict) -> dict:
    """Convert our JSON-Schema-ish dict to Gemini's OpenAPI-subset schema."""
    out: dict = {"type": _TYPE_MAP.get(schema.get("type", "string"), "STRING")}
    if "enum" in schema:
        out["type"] = "STRING"
        out["enum"] = schema["enum"]
    if "properties" in schema:
        out["type"] = "OBJECT"
        out["properties"] = {k: to_gemini_schema(v) for k, v in schema["properties"].items()}
    if "items" in schema:
        out["type"] = "ARRAY"
        out["items"] = to_gemini_schema(schema["items"])
    return out


def _to_gemini_function(tool: dict) -> dict:
    """OpenAI tool ({function:{name,description,parameters}}) -> Gemini functionDeclaration."""
    fn = tool.get("function", tool)
    decl: dict = {"name": fn.get("name", "")}
    if fn.get("description"):
        decl["description"] = fn["description"]
    if fn.get("parameters"):
        decl["parameters"] = to_gemini_schema(fn["parameters"])
    return decl


def _gemini_error(status: int, text: str, _headers=None) -> errors.SynthrError | None:
    msg = gstatus = None
    try:
        body = jsonlib.loads(text)
        err = body.get("error") if isinstance(body, dict) else None
        if isinstance(err, dict):
            msg = err.get("message")
            gstatus = err.get("status")
    except ValueError:
        pass
    if status == 429 or gstatus == "RESOURCE_EXHAUSTED":
        return errors.provider_rate_limited(msg or "Gemini quota exhausted.")
    if gstatus in {"INVALID_ARGUMENT", "FAILED_PRECONDITION"} and msg:
        return errors.provider_error(f"Gemini: {msg}")
    if msg:
        return errors.provider_error(f"Gemini: {msg}")
    return None


def _split_parts(parts: list[dict]) -> tuple[str, list[ToolCall]]:
    text_chunks: list[str] = []
    tool_calls: list[ToolCall] = []
    for part in parts or []:
        if "text" in part:
            text_chunks.append(part["text"])
        elif "functionCall" in part:
            call = part["functionCall"]
            tool_calls.append(ToolCall(id="", name=call.get("name", ""), arguments=jsonlib.dumps(call.get("args", {}))))
    return "".join(text_chunks), tool_calls


class GeminiProvider(Provider):
    capabilities = {Capability.TEXT, Capability.IMAGE, Capability.EMBED}
    supports_streaming = True
    supports_tools = True
    BASE = "https://generativelanguage.googleapis.com/v1beta"
    IMAGE_DEFAULT_MODEL = "imagen-4.0-generate-001"
    EMBED_DEFAULT_MODEL = "text-embedding-004"

    def __init__(self, name: str, *, api_key: str | None, default_model: str = "gemini-flash-latest") -> None:
        self.name = name
        self.api_key = api_key
        self.default_model = default_model

    def _body(self, messages: list[Message], json_schema: dict | None, temperature: float, tools: list[dict] | None) -> dict:
        system = "\n".join(m.content for m in messages if m.role == "system")
        user = "\n".join(m.content for m in messages if m.role != "system")

        gen_cfg: dict = {"temperature": temperature}
        if json_schema is not None:
            gen_cfg["responseMimeType"] = "application/json"
            gen_cfg["responseSchema"] = to_gemini_schema(json_schema)

        body: dict = {
            "contents": [{"role": "user", "parts": [{"text": user}]}],
            "generationConfig": gen_cfg,
        }
        if system:
            body["systemInstruction"] = {"parts": [{"text": system}]}
        if tools:
            body["tools"] = [{"functionDeclarations": [_to_gemini_function(t) for t in tools]}]
        return body

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
        tools: list[dict] | None = None,
    ) -> CompletionResult:
        model = model or self.default_model
        body = self._body(messages, json_schema, temperature, tools)
        url = f"{self.BASE}/models/{model}:generateContent?key={self.api_key}"
        data = await post_json(url, json=body, classify_error=_gemini_error)

        candidates = data.get("candidates")
        if not candidates:
            if (data.get("promptFeedback") or {}).get("blockReason"):
                raise errors.provider_safety_blocked("Gemini blocked the prompt on safety grounds.")
            raise errors.provider_invalid_response("Gemini returned no candidates.")
        candidate = candidates[0]
        if candidate.get("finishReason") == "SAFETY":
            raise errors.provider_safety_blocked("Gemini blocked the response on safety grounds.")

        text, tool_calls = _split_parts((candidate.get("content") or {}).get("parts", []))
        if not text and not tool_calls:
            raise errors.provider_invalid_response("Gemini completion response was malformed.")
        meta = data.get("usageMetadata", {})
        return CompletionResult(
            text=text,
            model=model,
            usage={
                "prompt_tokens": meta.get("promptTokenCount", 0),
                "completion_tokens": meta.get("candidatesTokenCount", 0),
            },
            raw=data,
            tool_calls=tool_calls,
            finish_reason=candidate.get("finishReason"),
        )

    async def stream_complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        model = model or self.default_model
        body = self._body(messages, None, temperature, None)
        url = f"{self.BASE}/models/{model}:streamGenerateContent?alt=sse&key={self.api_key}"
        async for chunk in post_sse(url, json=body, classify_error=_gemini_error):
            try:
                parts = chunk["candidates"][0]["content"]["parts"]
            except (KeyError, IndexError, TypeError):
                continue
            for part in parts:
                if part.get("text"):
                    yield part["text"]

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str | None = None,
        n: int = 1,
    ) -> ImageResult:
        model = model or self.IMAGE_DEFAULT_MODEL
        body = {"instances": [{"prompt": prompt}], "parameters": {"sampleCount": n}}
        url = f"{self.BASE}/models/{model}:predict?key={self.api_key}"
        data = await post_json(url, json=body, timeout=120, classify_error=_gemini_error)

        images = [
            {"b64": p["bytesBase64Encoded"], "mime": p.get("mimeType", "image/png")}
            for p in data.get("predictions", [])
            if p.get("bytesBase64Encoded")
        ]
        if not images:
            raise errors.provider_invalid_response("Gemini image response had no predictions.")
        return ImageResult(images=images, model=model, raw=data)

    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbedResult:
        model = model or self.EMBED_DEFAULT_MODEL
        body = {"requests": [{"model": f"models/{model}", "content": {"parts": [{"text": t}]}} for t in texts]}
        url = f"{self.BASE}/models/{model}:batchEmbedContents?key={self.api_key}"
        data = await post_json(url, json=body, classify_error=_gemini_error)
        vectors = [e.get("values", []) for e in data.get("embeddings", [])]
        if not vectors:
            raise errors.provider_invalid_response("Gemini returned no embeddings.")
        return EmbedResult(vectors=vectors, model=model)
