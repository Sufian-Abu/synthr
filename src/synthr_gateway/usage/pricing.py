"""Rough USD pricing per 1M tokens (input, output) for cost estimation.

Public list-price ballparks; 0 = free/local/unknown. Used to show approximate spend on
the dashboard — not billing-grade.
"""

from __future__ import annotations

# provider -> { model | "_default": (usd_per_1M_input, usd_per_1M_output) }
PRICES: dict[str, dict[str, tuple[float, float]]] = {
    "gemini": {"_default": (0.075, 0.30)},
    "openai": {"_default": (0.15, 0.60), "gpt-4o": (2.5, 10.0)},
    "grok": {"_default": (2.0, 10.0)},
    "groq": {"_default": (0.59, 0.79)},
    "ollama": {"_default": (0.0, 0.0)},
    "rembg": {"_default": (0.0, 0.0)},
    "mock": {"_default": (0.0, 0.0)},
}


def estimate_usd(provider: str, model: str | None, prompt_tokens: int, completion_tokens: int) -> float:
    table = PRICES.get(provider, {})
    in_rate, out_rate = table.get(model or "") or table.get("_default") or (0.0, 0.0)
    return (prompt_tokens * in_rate + completion_tokens * out_rate) / 1_000_000
