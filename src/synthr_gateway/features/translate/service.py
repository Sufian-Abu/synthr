"""translate orchestration."""

from __future__ import annotations

from ...providers import Provider
from ..common import run_text
from .models import TranslateRequest

SYSTEM = "You are a professional translator. Output only the translation — no notes or quotes."


async def translate(req: TranslateRequest, provider: Provider, model: str | None) -> tuple[dict, dict]:
    text, usage = await run_text(provider, model, SYSTEM, f"Translate to {req.target_lang}:\n\n{req.text}")
    return {"translation": text}, usage
