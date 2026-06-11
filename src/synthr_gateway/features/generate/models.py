"""Request model for generate (freeform text — the escape hatch)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    prompt: str = Field(min_length=1)
    max_words: int | None = Field(default=None, ge=1)

    model_config = {
        "json_schema_extra": {"examples": [{"prompt": "Write a one-line product tagline for a self-hosted AI gateway."}]}
    }
