"""Builds live provider instances from config: provider name -> Provider object."""

from __future__ import annotations

from ..config import Config
from .base import Provider
from .gemini import GeminiProvider
from .mock import MockProvider
from .openai_compat import OpenAICompatProvider
from .rembg import RembgProvider


def build_providers(config: Config) -> dict[str, Provider]:
    providers: dict[str, Provider] = {}
    for name, cfg in config.providers.items():
        if cfg.kind in ("openai", "grok", "groq", "ollama"):
            providers[name] = OpenAICompatProvider(name, cfg.kind, api_key=cfg.api_key, base_url=cfg.base_url)
        elif cfg.kind == "gemini":
            providers[name] = GeminiProvider(name, api_key=cfg.api_key)
        elif cfg.kind == "mock":
            providers[name] = MockProvider(name)
        elif cfg.kind == "rembg":
            providers[name] = RembgProvider(name)
    return providers
