"""Request model for seo (content -> title / description / keywords)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SeoRequest(BaseModel):
    content: str = Field(min_length=1)

    model_config = {
        "json_schema_extra": {
            "examples": [{"content": "Synthr is a self-hosted gateway that gives every project ready-made AI features."}]
        }
    }
