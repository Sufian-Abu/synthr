"""Hugging Face Inference adapter — text-to-image.

POSTs a prompt to the HF Inference API and returns the raw image bytes as base64. Free with
a HF token (hf_…). Image models such as `black-forest-labs/FLUX.1-schnell` or
`stabilityai/stable-diffusion-xl-base-1.0` work here; pick the model in config.
"""

from __future__ import annotations

import base64

import httpx

from ..core import errors
from .base import Provider
from .types import Capability, ImageResult

DEFAULT_BASE = "https://router.huggingface.co/hf-inference/models"
DEFAULT_MODEL = "black-forest-labs/FLUX.1-schnell"


class HuggingFaceProvider(Provider):
    capabilities = {Capability.IMAGE}

    def __init__(self, name: str, *, api_key: str | None = None, base_url: str | None = None,
                 default_model: str = DEFAULT_MODEL) -> None:
        self.name = name
        self.api_key = api_key
        self.base_url = (base_url or DEFAULT_BASE).rstrip("/")
        self.default_model = default_model

    async def generate_image(
        self,
        prompt: str,
        *,
        model: str | None = None,
        size: str | None = None,
        n: int = 1,
    ) -> ImageResult:
        model = model or self.default_model
        headers = {"Accept": "image/png"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=120) as client:
                resp = await client.post(f"{self.base_url}/{model}", json={"inputs": prompt}, headers=headers)
        except httpx.TimeoutException as exc:
            raise errors.provider_timeout() from exc
        except httpx.TransportError as exc:
            raise errors.provider_error(f"Network error contacting Hugging Face: {exc}") from exc

        ctype = resp.headers.get("content-type", "")
        if resp.status_code == 200 and ctype.startswith("image/"):
            return ImageResult(
                images=[{"b64": base64.b64encode(resp.content).decode(), "mime": ctype.split(";")[0] or "image/png"}],
                model=model,
            )

        # Error path — HF returns JSON.
        try:
            body = resp.json()
        except ValueError:
            body = {}
        detail = (body.get("error") if isinstance(body, dict) else None) or (resp.text[:200] if hasattr(resp, "text") else "")
        if resp.status_code == 503 and isinstance(body, dict) and body.get("estimated_time"):
            raise errors.provider_error(f"Hugging Face model {model!r} is warming up (~{int(body['estimated_time'])}s) — retry shortly.")
        if resp.status_code == 401:
            raise errors.provider_error("Hugging Face rejected the token (401) — set a valid HF_TOKEN.")
        if resp.status_code == 403:
            raise errors.provider_error(
                "Hugging Face token lacks Inference permission (403) — create a token with "
                "'Make calls to Inference Providers' enabled (or a classic read token)."
            )
        if resp.status_code == 429:
            raise errors.provider_rate_limited("Hugging Face rate limit hit.")
        raise errors.provider_error(f"Hugging Face image generation failed (HTTP {resp.status_code}). {detail}")
