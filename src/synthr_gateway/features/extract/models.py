"""Request model for extract (pull a LIST of structured records from text)."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ExtractField(BaseModel):
    name: str
    type: str = "string"  # string | number | integer | boolean
    description: str | None = None


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1)
    fields: list[ExtractField] = Field(min_length=1)  # the shape of each record

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fields": [
                        {"name": "item", "type": "string"},
                        {"name": "qty", "type": "integer"},
                        {"name": "price", "type": "number"},
                    ],
                    "text": "2x Coffee $9.00, 1x Bagel $3.50, 3x Water $6",
                }
            ]
        }
    }
