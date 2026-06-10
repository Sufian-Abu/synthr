"""Parse + validate the model's JSON output against the requested fields."""

from __future__ import annotations

import json
import re
from typing import Any

from .models import FormField


def extract_json(text: str) -> str:
    """Pull the first {...} block out of a response (handles ```json fences/prose)."""
    match = re.search(r"\{.*\}", text.strip(), re.DOTALL)
    return match.group(0) if match else text


def coerce_value(value: Any, field: FormField) -> Any:
    if value is None:
        return None
    if field.options is not None:
        return value if value in field.options else None
    try:
        if field.type == "number":
            return None if isinstance(value, bool) else float(value)
        if field.type == "integer":
            return None if isinstance(value, bool) else int(value)
        if field.type == "boolean":
            if isinstance(value, bool):
                return value
            if isinstance(value, str):
                return value.strip().lower() in ("true", "yes", "1")
            return bool(value)
        return str(value)
    except (ValueError, TypeError):
        return None


def parse_values(text: str, fields: list[FormField]) -> dict | None:
    """Return {field: coerced_value}, or None if the text isn't a valid JSON object."""
    try:
        obj = json.loads(extract_json(text))
    except (json.JSONDecodeError, TypeError):
        return None
    if not isinstance(obj, dict):
        return None
    return {f.name: coerce_value(obj.get(f.name), f) for f in fields}
