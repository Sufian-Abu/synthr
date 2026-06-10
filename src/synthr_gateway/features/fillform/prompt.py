"""Prompt construction for fillForm (internal — engineers never see this)."""

from __future__ import annotations

import json

from ...optimizer import compress
from .models import FillFormRequest

SYSTEM_PROMPT = (
    "You extract values for a set of form fields from the provided context. "
    "Respond with ONLY a JSON object whose keys are the field names. "
    "Use null for any field whose value is not present in the context — never guess. "
    "For fields with allowed options, choose only from that list (or null)."
)

RETRY_NUDGE = "Output ONLY valid JSON matching the field names. No prose."


def build_user_prompt(req: FillFormRequest) -> str:
    context = req.context if isinstance(req.context, str) else json.dumps(req.context, default=str)
    lines = ["Fields:"]
    for f in req.fields:
        opts = f" (options: {f.options})" if f.options else ""
        desc = f" — {f.description}" if f.description else ""
        lines.append(f"- {f.name} ({f.type}){opts}{desc}")
    if req.locale:
        lines.append(f"\nLocale: {req.locale}")
    lines.append(f"\nContext:\n{context}")
    return compress("\n".join(lines))
