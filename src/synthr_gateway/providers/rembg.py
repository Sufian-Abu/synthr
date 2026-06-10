"""Local background-removal provider (non-LLM) backed by rembg / U2Net.

rembg is an optional, heavy dependency (onnxruntime + model weights), so it is imported
lazily — installing the `vision` extra enables it; the rest of the gateway never needs it.
This is the proof that "any provider per feature" holds for non-text models.
"""

from __future__ import annotations

import asyncio

from ..core import errors
from .base import Provider
from .types import Capability


class RembgProvider(Provider):
    capabilities = {Capability.REMOVE_BACKGROUND}

    def __init__(self, name: str, *, model: str = "u2net") -> None:
        self.name = name
        self.model = model
        self._session = None

    def _session_or_raise(self):
        if self._session is None:
            try:
                from rembg import new_session
            except ImportError as exc:
                raise errors.provider_error(
                    "Background removal needs the 'vision' extra: pip install 'synthr-gateway[vision]'"
                ) from exc
            self._session = new_session(self.model)
        return self._session

    async def remove_background(self, image: bytes) -> bytes:
        def _run() -> bytes:
            session = self._session_or_raise()  # raises a clean error if rembg is missing
            from rembg import remove

            return remove(image, session=session)

        return await asyncio.to_thread(_run)  # rembg is sync/CPU-bound
