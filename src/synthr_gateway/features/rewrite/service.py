"""rewrite orchestration — transform text per an instruction."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_text
from .models import RewriteRequest

SYSTEM = "You rewrite text exactly as instructed. Output only the rewritten text — no notes, no quotes."


async def rewrite(req: RewriteRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    text, usage = await run_text(provider, model, SYSTEM, f"Instruction: {req.instruction}\n\nText:\n{req.text}")
    return {"text": text}, usage
