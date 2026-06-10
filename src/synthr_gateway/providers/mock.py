"""Deterministic provider with no network — for dev and CI without any key.

- complete(): given a JSON schema, returns an object with every property set to null.
- generate_image(): returns a tiny fixed base64 PNG placeholder.

Exercises the full pipeline (build -> call -> parse/shape -> envelope) with no live model.
"""

from __future__ import annotations

import base64
import json

from .base import Provider
from .types import Capability, CompletionResult, ImageResult, Message

_FAKE_PNG_B64 = base64.b64encode(b"mock-image").decode()


class MockProvider(Provider):
    capabilities = {Capability.TEXT, Capability.IMAGE, Capability.REMOVE_BACKGROUND}

    def __init__(self, name: str = "mock") -> None:
        self.name = name

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
    ) -> CompletionResult:
        if json_schema and "properties" in json_schema:
            text = json.dumps({key: None for key in json_schema["properties"]})
        else:
            text = next((m.content for m in reversed(messages)), "")
        return CompletionResult(text=text, model=model or "mock", usage={"prompt_tokens": 0, "completion_tokens": 0})

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str | None = None,
        n: int = 1,
    ) -> ImageResult:
        images = [{"b64": _FAKE_PNG_B64, "mime": "image/png"} for _ in range(n)]
        return ImageResult(images=images, model=model or "mock")

    async def remove_background(self, image: bytes) -> bytes:
        return image  # echo the input — exercises the pipeline without a model
