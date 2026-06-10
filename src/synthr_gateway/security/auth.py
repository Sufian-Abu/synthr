"""Project-key auth + dual-key / origin model (SPEC.md §2).

- secret keys (sk_proj_): backend/REST, full access.
- public keys  (pk_proj_): browser-safe — must come from an allowed origin and may only
  call features marked frontend_safe.
"""

from __future__ import annotations

from dataclasses import dataclass

from ..config import Config, FeatureCfg
from ..core import errors


@dataclass
class AuthContext:
    project_id: str
    key_id: str
    key_type: str  # "secret" | "public"
    allowed_origins: list[str]


def authenticate(config: Config, key: str | None, origin: str | None) -> AuthContext:
    if not key:
        raise errors.invalid_key()
    for project_id, project in config.projects.items():
        for k in project.keys:
            if k.id == key:
                if k.type == "public" and (not origin or origin not in k.allowed_origins):
                    raise errors.origin_not_allowed(origin)
                return AuthContext(project_id, k.id, k.type, k.allowed_origins)
    raise errors.invalid_key()


def authorize_feature(auth: AuthContext, feature_name: str, feature_cfg: FeatureCfg) -> None:
    if auth.key_type == "public" and not feature_cfg.frontend_safe:
        raise errors.feature_not_allowed(feature_name)
