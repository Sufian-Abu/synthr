"""Request model for embed (text -> vector)."""

from __future__ import annotations

from pydantic import BaseModel


class EmbedRequest(BaseModel):
    input: str | list[str]  # one string or a batch

    model_config = {"json_schema_extra": {"examples": [{"input": ["hello world", "goodbye world"]}]}}
