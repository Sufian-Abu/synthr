"""Output guardrails: redact PII that leaks into a response (SPEC.md §4.4).

Config-gated per feature (`redact_output_pii`) so it's only enabled on text features —
it walks string values and replaces detected PII with placeholders. Never enable it for
image/byte responses (it would corrupt base64).
"""

from __future__ import annotations

import re
from typing import Any

from ..config.schema import FeatureGuardrailsCfg

# Order matters: cards/SSNs before the looser phone pattern.
_REDACTIONS = [
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[redacted-email]"),
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[redacted-ssn]"),
    (re.compile(r"\b(?:\d[ -]?){13,19}\b"), "[redacted-card]"),
    (re.compile(r"\b(?:\+?\d{1,2}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b"), "[redacted-phone]"),
]


def _redact_text(text: str) -> tuple[str, bool]:
    found = False
    for pattern, placeholder in _REDACTIONS:
        text, n = pattern.subn(placeholder, text)
        found = found or n > 0
    return text, found


def _walk(value: Any) -> tuple[Any, bool]:
    if isinstance(value, str):
        return _redact_text(value)
    if isinstance(value, dict):
        found = False
        out = {}
        for key, val in value.items():
            out[key], hit = _walk(val)
            found = found or hit
        return out, found
    if isinstance(value, list):
        found = False
        out = []
        for val in value:
            new, hit = _walk(val)
            out.append(new)
            found = found or hit
        return out, found
    return value, False


def apply_output(data: dict, cfg: FeatureGuardrailsCfg) -> tuple[dict, bool]:
    """Return (possibly-redacted data, whether anything was redacted)."""
    if not cfg.redact_output_pii:
        return data, False
    return _walk(data)
