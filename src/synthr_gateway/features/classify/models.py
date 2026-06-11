"""Request model for classify (single-label classification over caller-defined labels)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ClassifyRequest(BaseModel):
    text: str = Field(min_length=1)
    labels: list[str] = Field(min_length=2)  # caller-defined, dynamic

    model_config = {
        "json_schema_extra": {
            "examples": [{"text": "The checkout keeps crashing and I'm furious.", "labels": ["bug", "praise", "question"]}]
        }
    }
