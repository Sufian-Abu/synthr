"""Request models and the JSON schema derived from the requested fields."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

_JSON_TYPES = {"string", "number", "integer", "boolean"}


class FormField(BaseModel):
    name: str
    type: str = "string"  # string | number | integer | boolean
    description: str | None = None
    options: list[Any] | None = None


class FillFormRequest(BaseModel):
    fields: list[FormField]
    context: Any
    locale: str | None = None

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "fields": [
                        {"name": "fullName", "type": "string"},
                        {"name": "size", "type": "number"},
                        {"name": "color", "type": "string", "options": ["red", "blue", "black"]},
                        {"name": "inStock", "type": "boolean"},
                    ],
                    "context": "John wants the Nike Air Max in red, size 10, and it's available now.",
                }
            ]
        }
    }


def build_field_schema(fields: list[FormField]) -> dict:
    """JSON schema the provider must return — one property per field."""
    properties: dict = {}
    for f in fields:
        spec: dict = {"type": f.type if f.type in _JSON_TYPES else "string"}
        if f.options:
            spec["enum"] = f.options
        properties[f.name] = spec
    return {"type": "object", "properties": properties}
