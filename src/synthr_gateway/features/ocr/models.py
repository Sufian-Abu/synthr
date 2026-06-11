"""Request model for ocr — read the text in an image."""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class OcrRequest(BaseModel):
    image: str | None = None  # base64 or data URI
    image_url: str | None = None

    model_config = {"json_schema_extra": {"examples": [{"image_url": "https://example.com/receipt.jpg"}]}}

    @model_validator(mode="after")
    def _need_one(self) -> OcrRequest:
        if not self.image and not self.image_url:
            raise ValueError("provide 'image' (base64/data-URI) or 'image_url'")
        return self
