"""One adapter for every OpenAI-compatible provider.

OpenAI, xAI Grok, and Ollama all expose the same `/chat/completions` API — they differ
only by base URL and whether a key is needed. So they share this adapter; `kind` in
config selects the default base URL. OpenAI and Grok also support `/images/generations`.
"""

from __future__ import annotations

from ..core import errors
from .base import Provider
from .http import post_json
from .types import Capability, CompletionResult, ImageResult, Message

DEFAULT_BASE_URL = {
    "openai": "https://api.openai.com/v1",
    "grok": "https://api.x.ai/v1",            # xAI Grok
    "groq": "https://api.groq.com/openai/v1",  # Groq fast inference (Llama, etc.)
    "ollama": "http://localhost:11434/v1",
}

IMAGE_KINDS = {"openai", "grok"}  # Groq/Ollama are text-only
IMAGE_DEFAULT_MODEL = {"openai": "gpt-image-1", "grok": "grok-2-image"}


class OpenAICompatProvider(Provider):
    def __init__(self, name: str, kind: str, *, api_key: str | None = None, base_url: str | None = None) -> None:
        self.name = name
        self.kind = kind
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE_URL[kind]).rstrip("/")
        self.capabilities = {Capability.TEXT}
        if kind in IMAGE_KINDS:
            self.capabilities.add(Capability.IMAGE)

    @property
    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.api_key}"} if self.api_key else {}

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
    ) -> CompletionResult:
        payload: dict = {
            "model": model,
            "messages": [{"role": m.role, "content": m.content} for m in messages],
            "temperature": temperature,
        }
        # JSON mode works on OpenAI/Grok and recent Ollama. The system prompt also
        # instructs JSON, which is the required fallback if a server ignores this.
        if json_schema is not None:
            payload["response_format"] = {"type": "json_object"}

        data = await post_json(f"{self.base_url}/chat/completions", json=payload, headers=self._headers)
        try:
            choice = data["choices"][0]
            content = choice["message"]["content"]
        except (KeyError, IndexError, TypeError) as exc:
            raise errors.provider_invalid_response(f"{self.kind}: malformed completion response.") from exc
        if choice.get("finish_reason") == "content_filter":
            raise errors.provider_safety_blocked(f"{self.kind} blocked the content.")

        usage = data.get("usage", {})
        return CompletionResult(
            text=content,
            model=model or "",
            usage={
                "prompt_tokens": usage.get("prompt_tokens", 0),
                "completion_tokens": usage.get("completion_tokens", 0),
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
        model = model or IMAGE_DEFAULT_MODEL.get(self.kind, "")
        payload: dict = {"model": model, "prompt": prompt, "n": n, "response_format": "b64_json"}
        if self.kind == "openai" and size:  # xAI's image API doesn't take `size`
            payload["size"] = size

        data = await post_json(
            f"{self.base_url}/images/generations", json=payload, headers=self._headers, timeout=120
        )

        images = []
        for item in data.get("data", []):
            if item.get("b64_json"):
                images.append({"b64": item["b64_json"], "mime": "image/png"})
            elif item.get("url"):
                images.append({"url": item["url"]})
        return ImageResult(images=images, model=model, raw=data)
