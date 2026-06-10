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
from pydantic import ValidationError

from .schema import Config

_ENV_PATTERN = re.compile(r"\$\{(\w+)\}|\$(\w+)")


class ConfigError(Exception):
    """Raised when synthr.config.yaml is missing, malformed, or inconsistent.

    The message is meant to be shown to a human as-is — it names the bad field.
    """


def _expand(value: Any) -> Any:
    if isinstance(value, str):
        return _ENV_PATTERN.sub(lambda m: os.environ.get(m.group(1) or m.group(2), ""), value)
    if isinstance(value, dict):
        return {k: _expand(v) for k, v in value.items()}
    if isinstance(value, list):
        return [_expand(v) for v in value]
    return value


def _format_validation_error(path: Path, exc: ValidationError) -> str:
    lines = [f"Invalid configuration in {path}:"]
    for err in exc.errors():
        loc = ".".join(str(p) for p in err["loc"]) or "(root)"
        lines.append(f"  - {loc}: {err['msg']}")
    return "\n".join(lines)


def _check_references(path: Path, config: Config) -> None:
    """Catch the most common mistake: a feature pointing at an undefined provider."""
    known = set(config.providers)
    problems: list[str] = []
    for name, feat in config.features.items():
        if feat.provider not in known:
            problems.append(
                f"feature '{name}': provider '{feat.provider}' is not defined under providers: "
                f"(have: {', '.join(sorted(known)) or 'none'})"
            )
        if feat.fallback and feat.fallback.provider not in known:
            problems.append(
                f"feature '{name}': fallback provider '{feat.fallback.provider}' is not defined under providers:"
            )
    if problems:
        raise ConfigError(f"Invalid configuration in {path}:\n" + "\n".join(f"  - {p}" for p in problems))


def load_config(path: str | Path | None = None) -> Config:
    """Load config. Defaults to $SYNTHR_CONFIG or ./synthr.config.yaml.

    A .env file in the working directory is loaded first (real exported env vars win),
    so API keys can live in .env instead of being exported by hand. On any problem,
    raises `ConfigError` with a human-readable message that names the offending field.
    """
    load_dotenv()  # no-op if there's no .env; never overrides already-set env vars
    path = Path(path or os.environ.get("SYNTHR_CONFIG", "synthr.config.yaml"))

    if not path.exists():
        raise ConfigError(f"Config file not found: {path}\nRun `synthr init` to scaffold one.")

    try:
        raw = yaml.safe_load(path.read_text())
    except yaml.YAMLError as exc:
        raise ConfigError(f"{path} is not valid YAML:\n  {exc}") from exc

    raw = raw or {}
    if not isinstance(raw, dict):
        raise ConfigError(f"{path} must be a mapping at the top level (got {type(raw).__name__}).")

    try:
        config = Config.model_validate(_expand(raw))
    except ValidationError as exc:
        raise ConfigError(_format_validation_error(path, exc)) from exc

    _check_references(path, config)
    return config
