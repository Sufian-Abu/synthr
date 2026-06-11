"""Startup security preflight.

Flags configuration that is fine for local dev but unsafe in production: a dev/placeholder
signing secret, plaintext (un-hashed) project keys, and browser-open public keys. Warnings
are logged on every boot; with SYNTHR_ENV=production they escalate to errors, and
SYNTHR_STRICT=1 refuses to start until they're resolved.
"""

from __future__ import annotations

import logging
import os

from .schema import Config

log = logging.getLogger("synthr_gateway")

_TRUTHY = {"1", "true", "yes", "on"}


def security_warnings(config: Config) -> list[str]:
    warnings: list[str] = []

    secret = (config.gateway.secret or "").strip()
    if not secret or "dev" in secret.lower():
        warnings.append("gateway.secret is unset or a dev placeholder — set a strong SYNTHR_SECRET.")

    for project_id, project in config.projects.items():
        for key in project.keys:
            if key.id and not key.hash:
                warnings.append(
                    f"project '{project_id}' has a plaintext key `id` (dev convenience) — "
                    "store a hashed key (`synthr keygen`) in production."
                )
            if key.type == "public" and not key.allowed_origins:
                warnings.append(
                    f"project '{project_id}' has a public key with no `allowed_origins` — "
                    "it is callable from any browser origin."
                )
    return warnings


def run_preflight(config: Config) -> None:
    """Log security warnings; escalate under production / strict mode."""
    warnings = security_warnings(config)
    if not warnings:
        return

    production = os.environ.get("SYNTHR_ENV", "").lower() == "production"
    strict = os.environ.get("SYNTHR_STRICT", "").lower() in _TRUTHY
    level = logging.ERROR if production else logging.WARNING
    banner = "INSECURE FOR PRODUCTION" if production else "security preflight"

    log.log(level, "Synthr %s — %d issue(s) found:", banner, len(warnings))
    for w in warnings:
        log.log(level, "  - %s", w)

    if strict:
        from .loader import ConfigError

        raise ConfigError("Refusing to start (SYNTHR_STRICT=1): resolve the security issues above.")
