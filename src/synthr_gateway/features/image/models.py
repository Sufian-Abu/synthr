"""Request model for image generation."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ImageRequest(BaseModel):
    prompt: str
    size: str = "1024x1024"
    n: int = Field(default=1, ge=1, le=4)

    model_config = {
        "json_schema_extra": {
            "examples": [{"prompt": "a minimalist red running shoe on a white background", "size": "1024x1024", "n": 1}]
        }
    }
