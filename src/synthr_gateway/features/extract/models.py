"""Request model for extract — pull structured data from text.

Two modes:
- `schema` (a {field: type} map) → **one** structured record, returned directly.
- `fields` (a list of field defs) → a **list** of records under `items`.
"""

from __future__ import annotations

from pydantic import BaseModel, Field, model_validator


class ExtractField(BaseModel):
    name: str
    type: str = "string"  # string | number | integer | boolean
    description: str | None = None


class ExtractRequest(BaseModel):
    text: str = Field(min_length=1)
    # one record: {"amount": "number", "vendor": "string", "date": "string"}
    schema_: dict[str, str] | None = Field(default=None, alias="schema")
    # many records: each row has these fields
    fields: list[ExtractField] | None = None

    model_config = {
        "populate_by_name": True,
        "json_schema_extra": {
            "examples": [
                {
                    "text": "Invoice 412 — Acme Corp billed $1,290.00 on 2026-02-01.",
                    "schema": {"amount": "number", "vendor": "string", "date": "string"},
                }
            ]
        },
    }

    @model_validator(mode="after")
    def _need_one(self) -> ExtractRequest:
        if not self.schema_ and not self.fields:
            raise ValueError("provide 'schema' (one record) or 'fields' (a list of records)")
        return self
