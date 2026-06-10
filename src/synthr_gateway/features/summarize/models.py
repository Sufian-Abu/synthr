"""Request model for summarize."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SummarizeRequest(BaseModel):
    text: str = Field(min_length=1)
    max_words: int | None = Field(default=None, ge=1)

    model_config = {
        "json_schema_extra": {
            "examples": [
                {"text": "Synthr is a self-hosted gateway that gives every project ready-made AI features behind one SDK.", "max_words": 12}
            ]
        }
    }
