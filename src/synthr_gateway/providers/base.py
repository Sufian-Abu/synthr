"""Provider interface. Every backend implements this, so features stay provider-agnostic.

Each capability method defaults to "not supported" and is overridden by providers that
offer it; `capabilities` declares which kinds, and `supports_streaming` / `supports_tools`
declare the optional text modes. The API layer checks these before calling.
"""

from __future__ import annotations

from abc import ABC
from collections.abc import AsyncIterator

from ..core import errors
from .types import Capability, CompletionResult, EmbedResult, ImageResult, Message


class Provider(ABC):
    """Subclasses set `name`, `capabilities`, the optional flags, and override what they support."""

    name: str
    capabilities: set[Capability] = set()
    supports_streaming: bool = False
    supports_tools: bool = False

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
        tools: list[dict] | None = None,
    ) -> CompletionResult:
        """Run a text completion. If `json_schema` is given, the provider returns JSON
        conforming to it (enforced natively where supported). If `tools` is given (OpenAI
        function-tool format), tool calls come back on `CompletionResult.tool_calls`."""
        raise errors.provider_error(f"Provider {self.name!r} does not support text completion.")

    async def stream_complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        temperature: float = 0.0,
    ) -> AsyncIterator[str]:
        """Yield text deltas as they arrive. Only providers with `supports_streaming` override this."""
        raise errors.provider_error(f"Provider {self.name!r} does not support streaming.")
        yield ""  # pragma: no cover — marks this as an async generator

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str | None = None,
        n: int = 1,
    ) -> ImageResult:
        raise errors.provider_error(f"Provider {self.name!r} does not support image generation.")

    async def remove_background(self, image: bytes) -> bytes:
        """Return a transparent PNG with the background removed."""
        raise errors.provider_error(f"Provider {self.name!r} does not support background removal.")

    async def embed(self, texts: list[str], *, model: str | None = None) -> EmbedResult:
        """Return one embedding vector per input text."""
        raise errors.provider_error(f"Provider {self.name!r} does not support embeddings.")

    async def vision(
        self,
        prompt: str,
        *,
        image_b64: str | None = None,
        image_url: str | None = None,
        mime: str = "image/png",
        model: str | None = None,
    ) -> CompletionResult:
        """Answer `prompt` about an image (OCR, captioning). Image as base64 or a URL."""
        raise errors.provider_error(f"Provider {self.name!r} does not support vision.")
