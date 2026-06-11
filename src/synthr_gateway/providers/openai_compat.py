"""OpenAI-compatible providers — one base, one subclass per provider.

OpenAI, xAI Grok, Groq, and Ollama all speak the `/chat/completions` API, but they are
*close, not identical*. The base class holds the shared request/response shape; each
subclass overrides where it genuinely differs:

- **JSON mode:** OpenAI uses strict `json_schema` structured output; Grok/Groq/Ollama use
  `json_object`.
- **Image API:** only OpenAI and Grok generate images, with different default models, and
  xAI ignores `size`.
- **Errors:** each provider's error *body* is parsed into a typed `SynthrError`.
- **Streaming & tools:** shared OpenAI-style SSE deltas and `tool_calls` parsing.
"""

from __future__ import annotations

import json as jsonlib
from collections.abc import AsyncIterator

from ..core import errors
from .base import Provider
from .http import post_json, post_sse
from .types import Capability, CompletionResult, EmbedResult, ImageResult, Message, ToolCall

DEFAULT_BASE_URL = {
    "openai": "https://api.openai.com/v1",
    "grok": "https://api.x.ai/v1",
    "groq": "https://api.groq.com/openai/v1",
    "ollama": "http://localhost:11434/v1",
}


def _strict_schema(schema: dict) -> dict:
    """OpenAI structured outputs require every object to be closed (all props required,
    additionalProperties: false). Recursively rewrite our simple schema to satisfy that."""
    if not isinstance(schema, dict):
        return schema
    out = dict(schema)
    if out.get("type") == "object" and "properties" in out:
        out["properties"] = {k: _strict_schema(v) for k, v in out["properties"].items()}
        out["required"] = list(out["properties"].keys())
        out["additionalProperties"] = False
    if out.get("type") == "array" and "items" in out:
        out["items"] = _strict_schema(out["items"])
    return out


def _openai_error(status: int, text: str, _headers=None) -> errors.SynthrError | None:
    """Parse an OpenAI/Grok/Groq error body ({"error": {message, type, code}})."""
    code = msg = None
    try:
        body = jsonlib.loads(text)
        err = body.get("error") if isinstance(body, dict) else None
        if isinstance(err, dict):
            code = err.get("code") or err.get("type") or ""
            msg = err.get("message")
        elif isinstance(err, str):
            msg = err
    except ValueError:
        pass
    blob = f"{code} {msg}".lower()
    if status == 429 or "rate_limit" in blob or ("rate" in blob and "limit" in blob):
        return errors.provider_rate_limited(msg or "Provider rate limit hit.")
    if "content_filter" in blob or "content_policy" in blob or "safety" in blob:
        return errors.provider_safety_blocked(msg or "Blocked by provider safety policy.")
    if msg:
        return errors.provider_error(f"{msg}")
    return None  # fall back to generic status mapping


def _ollama_error(status: int, text: str, _headers=None) -> errors.SynthrError | None:
    """Ollama errors are {"error": "free text"} rather than the OpenAI envelope."""
    try:
        body = jsonlib.loads(text)
        msg = body.get("error") if isinstance(body, dict) else None
    except ValueError:
        msg = None
    if status == 429:
        return errors.provider_rate_limited(msg or "Ollama is busy.")
    if msg:
        return errors.provider_error(f"Ollama: {msg}")
    return None


def _parse_tool_calls(raw: list | None) -> list[ToolCall]:
    calls: list[ToolCall] = []
    for tc in raw or []:
        fn = (tc or {}).get("function", {}) or {}
        calls.append(ToolCall(id=tc.get("id", ""), name=fn.get("name", ""), arguments=fn.get("arguments", "")))
    return calls


class OpenAICompatProvider(Provider):
    """Base for every OpenAI-compatible provider. Subclasses set `kind` and override quirks."""

    kind: str = "openai"
    supports_tools = True
    supports_streaming = True
    supports_images = False
    supports_embeddings = False
    image_endpoint = "/images/generations"
    image_default_model: str | None = None
    image_supports_size = True
    embed_default_model = ""

    def __init__(self, name: str, *, api_key: str | None = None, base_url: str | None = None) -> None:
        self.name = name
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL[self.kind]).rstrip("/")
        self.capabilities = {Capability.TEXT}
        if self.supports_images:
            self.capabilities.add(Capability.IMAGE)
        if self.supports_embeddings:
            self.capabilities.add(Capability.EMBED)

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    # ── per-provider hooks ────────────────────────────────────────────────
    def _apply_json_mode(self, payload: dict, json_schema: dict) -> None:
        payload["response_format"] = {"type": "json_object"}

    def _classify_error(self, status: int, text: str, headers=None) -> errors.SynthrError | None:
        return _openai_error(status, text, headers)

    def _messages(self, messages: list[Message]) -> list[dict]:
        return [{"role": m.role, "content": m.content} for m in messages]

    # ── text ──────────────────────────────────────────────────────────────
    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
        tools: list[dict] | None = None,
    ) -> CompletionResult:
        payload: dict = {"model": model, "messages": self._messages(messages), "temperature": temperature}
        if json_schema is not None:
            self._apply_json_mode(payload, json_schema)
        if tools:
            payload["tools"] = tools
            payload["tool_choice"] = "auto"

        data = await post_json(
            f"{self.base_url}/chat/completions", json=payload, headers=self._headers, classify_error=self._classify_error
        )
        try:
            choice = data["choices"][0]
            message = choice.get("message", {})
        except (KeyError, IndexError, TypeError) as exc:
            raise errors.provider_invalid_response(f"{self.kind}: malformed completion response.") from exc
        if choice.get("finish_reason") == "content_filter":
            raise errors.provider_safety_blocked(f"{self.kind} blocked the content.")

        usage = data.get("usage", {})
        return CompletionResult(
            text=message.get("content") or "",
            model=model or "",
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
            },
            raw=data,
            tool_calls=_parse_tool_calls(message.get("tool_calls")),
            finish_reason=choice.get("finish_reason"),
        )

    async def stream_complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        payload = {"model": model, "messages": self._messages(messages), "temperature": temperature, "stream": True}
        async for chunk in post_sse(
            f"{self.base_url}/chat/completions", json=payload, headers=self._headers, classify_error=self._classify_error
        ):
            try:
                delta = chunk["choices"][0]["delta"].get("content")
            except (KeyError, IndexError, TypeError):
                continue
            if delta:
                yield delta

    # ── image ─────────────────────────────────────────────────────────────
    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str | None = None,
        n: int = 1,
    ) -> ImageResult:
        if not self.supports_images:
            raise errors.provider_error(f"{self.kind} does not support image generation.")
        model = model or self.image_default_model or ""
        payload: dict = {"model": model, "prompt": prompt, "n": n, "response_format": "b64_json"}
        if self.image_supports_size and size:
            payload["size"] = size

        data = await post_json(
            f"{self.base_url}{self.image_endpoint}",
            json=payload,
            headers=self._headers,
            timeout=120,
            classify_error=self._classify_error,
        )
        images = []
        for item in data.get("data", []):
            if item.get("b64_json"):
                images.append({"b64": item["b64_json"], "mime": "image/png"})
            elif item.get("url"):
                images.append({"url": item["url"]})
        if not images:
            raise errors.provider_invalid_response(f"{self.kind}: image response had no data.")
        return ImageResult(images=images, model=model, raw=data)

    # ── embeddings ────────────────────────────────────────────────────────
    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbedResult:
        if not self.supports_embeddings:
            raise errors.provider_error(f"{self.kind} does not support embeddings.")
        model = model or self.embed_default_model
        data = await post_json(
            f"{self.base_url}/embeddings",
            json={"model": model, "input": texts},
            headers=self._headers,
            classify_error=self._classify_error,
        )
        vectors = [row.get("embedding", []) for row in data.get("data", [])]
        if not vectors:
            raise errors.provider_invalid_response(f"{self.kind}: embeddings response had no data.")
        usage = data.get("usage", {})
        return EmbedResult(vectors=vectors, model=model, usage={"prompt_tokens": usage.get("prompt_tokens", 0)})


class OpenAIProvider(OpenAICompatProvider):
    kind = "openai"
    supports_images = True
    supports_embeddings = True
    image_default_model = "gpt-image-1"
    image_supports_size = True
    embed_default_model = "text-embedding-3-small"

    def _apply_json_mode(self, payload: dict, json_schema: dict) -> None:
        # OpenAI supports strict structured outputs — stronger than json_object.
        payload["response_format"] = {
            "type": "json_schema",
            "json_schema": {"name": "result", "schema": _strict_schema(json_schema), "strict": True},
        }


class GrokProvider(OpenAICompatProvider):
    kind = "grok"
    supports_images = True
    image_default_model = "grok-2-image"
    image_supports_size = False  # xAI's image API rejects `size`


class GroqProvider(OpenAICompatProvider):
    kind = "groq"
    supports_images = False  # Groq is text-only


class OllamaProvider(OpenAICompatProvider):
    kind = "ollama"
    supports_images = False  # text-only via the OpenAI-compat endpoint
    supports_embeddings = True
    embed_default_model = "nomic-embed-text"

    def _classify_error(self, status: int, text: str, headers=None) -> errors.SynthrError | None:
        return _ollama_error(status, text, headers)


KIND_TO_CLASS = {
    "openai": OpenAIProvider,
    "grok": GrokProvider,
    "groq": GroqProvider,
    "ollama": OllamaProvider,
}
