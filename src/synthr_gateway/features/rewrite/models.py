"""Request model for rewrite (grammar/tone/style transform)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class RewriteRequest(BaseModel):
    text: str = Field(min_length=1)
    instruction: str = "Fix grammar and improve clarity."

    model_config = {
        "json_schema_extra": {
            "examples": [{"text": "we was hoping you can maybe help us out", "instruction": "Make it formal and concise."}]
        }
    }
