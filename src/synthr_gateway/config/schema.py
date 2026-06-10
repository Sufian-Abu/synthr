"""Pydantic models for synthr.config.yaml (the runtime source of truth)."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field, model_validator

ProviderKind = Literal["openai", "grok", "groq", "ollama", "gemini", "rembg", "mock"]


class GatewayCfg(BaseModel):
    port: int = 8000
    secret: str = "dev-secret"
    db_path: str = "synthr.db"  # ":memory:" for ephemeral


class ProviderCfg(BaseModel):
    kind: ProviderKind
    api_key: str | None = None
    base_url: str | None = None  # optional override for openai-compatible providers


class CacheCfg(BaseModel):
    enabled: bool = False
    mode: Literal["exact", "similar"] = "exact"
    ttl_minutes: int = 60
    similarity_threshold: float = 0.85  # only used when mode == "similar"


class FeatureGuardrailsCfg(BaseModel):
    block_pii: bool = False
    max_prompt_length: int | None = None
    blocked_keywords: list[str] = Field(default_factory=list)
    validate_output: bool = True
    redact_output_pii: bool = False  # scrub PII from the response (text features only)


class FallbackCfg(BaseModel):
    provider: str
    model: str | None = None


class FeatureCfg(BaseModel):
    provider: str
    model: str | None = None
    frontend_safe: bool = False
    fallback: FallbackCfg | None = None
    cache: CacheCfg = CacheCfg()
    guardrails: FeatureGuardrailsCfg = FeatureGuardrailsCfg()


class KeyCfg(BaseModel):
    type: Literal["secret", "public"]
    hash: str | None = None  # sha256 hex of the key — store THIS in production, not the key
    id: str | None = None  # plaintext key — dev convenience only; hashed in memory at load
    allowed_origins: list[str] = Field(default_factory=list)
    scopes: list[str] = Field(default_factory=lambda: ["*"])  # feature names; ["*"] = all
    expires: str | None = None  # ISO date/datetime; None = never expires
    revoked: bool = False
    label: str | None = None  # non-secret identifier for logs / audit / dashboards

    @model_validator(mode="after")
    def _require_secret(self) -> KeyCfg:
        if not self.hash and not self.id:
            raise ValueError("each key needs 'hash' (preferred) or 'id' (plaintext, dev only)")
        return self


class LimitsCfg(BaseModel):
    per_user: dict[str, int] = Field(default_factory=dict)
    per_feature: dict[str, dict[str, int]] = Field(default_factory=dict)


class ProjectCfg(BaseModel):
    keys: list[KeyCfg] = Field(default_factory=list)
    limits: LimitsCfg = LimitsCfg()


class DefaultsCfg(BaseModel):
    limits: LimitsCfg = LimitsCfg()


class Config(BaseModel):
    gateway: GatewayCfg = GatewayCfg()
    providers: dict[str, ProviderCfg] = Field(default_factory=dict)
    features: dict[str, FeatureCfg] = Field(default_factory=dict)
    projects: dict[str, ProjectCfg] = Field(default_factory=dict)
    defaults: DefaultsCfg = DefaultsCfg()
