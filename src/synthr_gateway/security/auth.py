"""Project-key auth + dual-key / origin model.

- secret keys (sk_proj_): backend/REST, full access.
- public keys  (pk_proj_): browser-safe — must come from an allowed origin and may only
  call features marked frontend_safe.

Keys are matched by **sha256 hash** with a constant-time compare. Production configs store
only the hash; a plaintext `id` is accepted as a dev convenience and hashed at load. Keys
may also carry scopes, an expiry, and a revoked flag.
"""

from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass, field
from datetime import UTC, date, datetime

from ..config import Config, FeatureCfg, KeyCfg
from ..core import errors


@dataclass
class AuthContext:
    project_id: str
    key_id: str  # non-secret identifier (label or hash prefix) — safe to log
    key_type: str  # "secret" | "public"
    allowed_origins: list[str]
    scopes: list[str] = field(default_factory=lambda: ["*"])


def _sha256(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _stored_digest(key: KeyCfg) -> str | None:
    """The hash to compare against: explicit `hash`, else the hash of the plaintext `id`."""
    return key.hash or (_sha256(key.id) if key.id else None)


def _key_id(key: KeyCfg, digest: str) -> str:
    return key.label or f"key_{digest[:12]}"


def _is_expired(expires: str) -> bool:
    raw = expires.strip()
    try:
        if len(raw) == 10:  # date only, e.g. 2026-12-31
            return date.fromisoformat(raw) < datetime.now(UTC).date()
        moment = datetime.fromisoformat(raw)
        if moment.tzinfo is None:
            moment = moment.replace(tzinfo=UTC)
        return moment < datetime.now(UTC)
    except ValueError:
        return False  # unparseable — don't lock anyone out over a typo


def authenticate(config: Config, key: str | None, origin: str | None) -> AuthContext:
    if not key:
        raise errors.invalid_key()
    digest = _sha256(key)
    for project_id, project in config.projects.items():
        for k in project.keys:
            stored = _stored_digest(k)
            if stored and hmac.compare_digest(stored, digest):
                if k.revoked:
                    raise errors.key_revoked()
                if k.expires and _is_expired(k.expires):
                    raise errors.key_expired()
                if k.type == "public" and (not origin or origin not in k.allowed_origins):
                    raise errors.origin_not_allowed(origin)
                return AuthContext(project_id, _key_id(k, digest), k.type, k.allowed_origins, list(k.scopes))
    raise errors.invalid_key()


def authorize_feature(auth: AuthContext, feature_name: str, feature_cfg: FeatureCfg) -> None:
    if auth.key_type == "public" and not feature_cfg.frontend_safe:
        raise errors.feature_not_allowed(feature_name)
    if "*" not in auth.scopes and feature_name not in auth.scopes:
        raise errors.feature_not_allowed(feature_name)
