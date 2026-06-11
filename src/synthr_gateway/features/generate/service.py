"""generate orchestration — freeform prompt to text."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_text
from .models import GenerateRequest

SYSTEM = "You are a helpful assistant. Answer directly and concisely, with no preamble."


async def generate(req: GenerateRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    limit = f"Use at most about {req.max_words} words.\n\n" if req.max_words else ""
    text, usage = await run_text(provider, model, SYSTEM, f"{limit}{req.prompt}")
    return {"text": text}, usage
