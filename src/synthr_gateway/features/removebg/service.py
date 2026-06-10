"""removeBackground orchestration: get image bytes -> provider -> base64 PNG."""

from __future__ import annotations

import base64
import binascii

import httpx

from ...core import errors
from ...providers import Provider
from .models import RemoveBackgroundRequest


def _decode_base64(image: str) -> bytes:
    if image.startswith("data:"):  # strip a data-URI prefix if present
        image = image.split(",", 1)[-1]
    try:
        return base64.b64decode(image, validate=True)
    except (binascii.Error, ValueError) as exc:
        raise errors.invalid_input("'image' is not valid base64.") from exc


async def _load_bytes(req: RemoveBackgroundRequest) -> bytes:
    if req.image_url:
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.get(req.image_url)
                resp.raise_for_status()
                return resp.content
        except httpx.HTTPError as exc:
            raise errors.invalid_input(f"Could not fetch image_url: {exc}") from exc
    return _decode_base64(req.image or "")


async def remove_background(req: RemoveBackgroundRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    raw = await _load_bytes(req)
    output = await provider.remove_background(raw)
    b64 = base64.b64encode(output).decode()
    return {"image": {"b64": b64, "mime": "image/png"}}, {}
