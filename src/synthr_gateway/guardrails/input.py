"""Regex-based input guardrails (SPEC.md §4.4). Fast, free, ~90% effective.

Raises `guardrail_blocked` before the prompt is sent to any provider.
"""

from __future__ import annotations

import re

from ..config.schema import FeatureGuardrailsCfg
from ..core import errors

PII_PATTERNS = {
    "a credit card number": re.compile(r"\b(?:\d[ -]?){13,19}\b"),
    "an SSN": re.compile(r"\b\d{3}-\d{2}-\d{4}\b"),
    "an email address": re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"),
    "a phone number": re.compile(r"\b(?:\+?\d{1,2}[\s-]?)?\(?\d{3}\)?[\s-]?\d{3}[\s-]?\d{4}\b"),
}


def check_input(text: str | None, cfg: FeatureGuardrailsCfg) -> None:
    if not text:
        return

    if cfg.max_prompt_length is not None and len(text) > cfg.max_prompt_length:
        raise errors.guardrail_blocked(f"Input exceeds max length of {cfg.max_prompt_length} characters.")

    if cfg.block_pii:
        for label, pattern in PII_PATTERNS.items():
            if pattern.search(text):
                raise errors.guardrail_blocked(f"Input appears to contain {label}; blocked before sending.")

    if cfg.blocked_keywords:
        lowered = text.lower()
        for keyword in cfg.blocked_keywords:
            if keyword.lower() in lowered:
                raise errors.guardrail_blocked("Input contains a blocked keyword.")
