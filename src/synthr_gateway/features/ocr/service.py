"""ocr orchestration — image in, plain text out (vision capability)."""

from __future__ import annotations

from ...providers import Provider
from .models import OcrRequest

PROMPT = (
    "Extract all text from this image exactly as written, preserving line breaks and reading "
    "order. Return only the text, with no commentary."
)


def _split_data_uri(image: str) -> tuple[str | None, str]:
    """A data URI -> (base64, mime); a bare base64 string -> (it, image/png)."""
    if image.startswith("data:") and ";base64," in image:
        header, b64 = image.split(";base64,", 1)
        mime = header[len("data:"):] or "image/png"
        return b64, mime
    return image, "image/png"


async def ocr(req: OcrRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    image_b64: str | None = None
    mime = "image/png"
    if req.image:
        image_b64, mime = _split_data_uri(req.image)
    result = await provider.vision(PROMPT, image_b64=image_b64, image_url=req.image_url, mime=mime, model=model)
    return {"text": result.text.strip()}, result.usage
