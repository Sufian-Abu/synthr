"""Native Gemini adapter (generativelanguage REST API).

Gemini differs from OpenAI: system goes in `systemInstruction`, and structured output
is requested via `responseMimeType` + `responseSchema`.
"""

from __future__ import annotations

from ..core import errors
from .base import Provider
from .http import post_json
from .types import Capability, CompletionResult, ImageResult, Message

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


class GeminiProvider(Provider):
    capabilities = {Capability.TEXT, Capability.IMAGE}
    BASE = "https://generativelanguage.googleapis.com/v1beta"
    IMAGE_DEFAULT_MODEL = "imagen-3.0-generate-002"

    def __init__(self, name: str, *, api_key: str | None, default_model: str = "gemini-flash-latest") -> None:
        self.name = name
        self.api_key = api_key
        self.default_model = default_model

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
    ) -> CompletionResult:
        model = model or self.default_model
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

        url = f"{self.BASE}/models/{model}:generateContent?key={self.api_key}"
        data = await post_json(url, json=body)

        candidates = data.get("candidates")
        if not candidates:
            if (data.get("promptFeedback") or {}).get("blockReason"):
                raise errors.provider_safety_blocked("Gemini blocked the prompt on safety grounds.")
            raise errors.provider_invalid_response("Gemini returned no candidates.")
        candidate = candidates[0]
        if candidate.get("finishReason") == "SAFETY":
            raise errors.provider_safety_blocked("Gemini blocked the response on safety grounds.")
        try:
            text = candidate["content"]["parts"][0]["text"]
        except (KeyError, IndexError, TypeError) as exc:
            raise errors.provider_invalid_response("Gemini completion response was malformed.") from exc
        meta = data.get("usageMetadata", {})
        return CompletionResult(
            text=text,
            model=model,
            usage={
                "prompt_tokens": meta.get("promptTokenCount", 0),
                "completion_tokens": meta.get("candidatesTokenCount", 0),
            },
            raw=data,
        )

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
        data = await post_json(url, json=body, timeout=120)

        images = [
            {"b64": p["bytesBase64Encoded"], "mime": p.get("mimeType", "image/png")}
            for p in data.get("predictions", [])
            if p.get("bytesBase64Encoded")
        ]
        return ImageResult(images=images, model=model, raw=data)
