"""Request model for moderate (content-safety classification)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModerateRequest(BaseModel):
    text: str = Field(min_length=1)

    model_config = {"json_schema_extra": {"examples": [{"text": "I will find you and make you regret this."}]}}
