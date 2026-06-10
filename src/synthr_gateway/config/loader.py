"""Read YAML, expand ${ENV} references in string values, validate into Config.

Env expansion runs on the *parsed* structure (not the raw text) so that ${VAR}
placeholders are safe inside YAML flow mappings and don't corrupt the document.
"""

from __future__ import annotations

import os
import re
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .schema import Config

_ENV_PATTERN = re.compile(r"\$\{(\w+)\}|\$(\w+)")


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1) or m.group(2), ""), value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def load_config(path: str | Path | None = None) -> Config:
    """Load config. Defaults to $SYNTHR_CONFIG or ./synthr.config.yaml.

    A .env file in the working directory is loaded first (real exported env vars win),
    so API keys can live in .env instead of being exported by hand.
    """
    load_dotenv()  # no-op if there's no .env; never overrides already-set env vars
    path = Path(path or os.environ.get("SYNTHR_CONFIG", "synthr.config.yaml"))
    data = yaml.safe_load(path.read_text()) or {}
    return Config.model_validate(_expand(data))
