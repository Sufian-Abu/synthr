"""summarize orchestration."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_text
from .models import SummarizeRequest

SYSTEM = "You summarize text concisely and accurately. Return only the summary, no preamble."


async def summarize(req: SummarizeRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    limit = f"Use at most about {req.max_words} words.\n\n" if req.max_words else ""
    text, usage = await run_text(provider, model, SYSTEM, f"{limit}{req.text}")
    return {"summary": text}, usage
