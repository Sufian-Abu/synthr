"""Request model for translate."""

from __future__ import annotations

from pydantic import BaseModel, Field


class TranslateRequest(BaseModel):
    text: str = Field(min_length=1)
    target_lang: str = Field(min_length=1)  # e.g. "Spanish", "fr", "Japanese"

    model_config = {
        "json_schema_extra": {"examples": [{"text": "Good morning, how are you?", "target_lang": "Spanish"}]}
    }
