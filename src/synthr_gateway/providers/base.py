"""Provider interface. Every backend implements this, so features stay provider-agnostic.

Each capability method defaults to "not supported" and is overridden by providers that
offer it; `capabilities` declares which ones, and the API layer checks it before calling.
"""

from __future__ import annotations

from abc import ABC

from ..core import errors
from .types import Capability, CompletionResult, ImageResult, Message


class Provider(ABC):
    """Subclasses set `name`, `capabilities`, and override the methods they support."""

    name: str
    capabilities: set[Capability] = set()

    async def complete(
        self,
        messages: list[Message],
        *,
        model: str | None = None,
        json_schema: dict | None = None,
        temperature: float = 0.0,
    ) -> CompletionResult:
        """Run a text completion. If json_schema is given, the provider is asked to
        return JSON conforming to it (enforced natively where supported)."""
        raise errors.provider_error(f"Provider {self.name!r} does not support text completion.")

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
