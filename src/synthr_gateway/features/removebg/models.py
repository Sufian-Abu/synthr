"""Request model: an image as base64/data-URI, or a URL to fetch."""

from __future__ import annotations

from pydantic import BaseModel, model_validator


class RemoveBackgroundRequest(BaseModel):
    image: str | None = None  # base64 or data URI
    image_url: str | None = None

    model_config = {
        "json_schema_extra": {"examples": [{"image_url": "https://example.com/photo.jpg"}]}
    }

    @model_validator(mode="after")
    def _require_one(self) -> "RemoveBackgroundRequest":
        if not self.image and not self.image_url:
            raise ValueError("provide either 'image' (base64/data-URI) or 'image_url'")
        return self
