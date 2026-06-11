"""Startup security preflight: flags dev-secret, plaintext keys, open public keys."""

from __future__ import annotations

import pytest

from synthr_gateway.config import ConfigError
from synthr_gateway.config.preflight import run_preflight, security_warnings
from synthr_gateway.config.schema import Config


def _config(yaml_secret: str, keys: list[dict]) -> Config:
    return Config.model_validate(
        {
            "gateway": {"secret": yaml_secret},
            "providers": {"mock": {"kind": "mock"}},
            "projects": {"demo": {"keys": keys}},
        }
    )


def test_flags_dev_secret_and_plaintext_key() -> None:
    cfg = _config("dev-secret", [{"type": "secret", "id": "sk_proj_x"}])
    issues = security_warnings(cfg)
    assert any("secret" in w for w in issues)
    assert any("plaintext" in w for w in issues)


def test_flags_public_key_without_origins() -> None:
    cfg = _config("a-strong-secret", [{"type": "public", "hash": "abc"}])
    assert any("allowed_origins" in w for w in security_warnings(cfg))


def test_clean_config_has_no_warnings() -> None:
    cfg = _config("a-strong-secret", [{"type": "secret", "hash": "abc"}])
    assert security_warnings(cfg) == []


def test_strict_mode_refuses_to_start(monkeypatch) -> None:
    monkeypatch.setenv("SYNTHR_STRICT", "1")
    cfg = _config("dev-secret", [{"type": "secret", "id": "sk_proj_x"}])
    with pytest.raises(ConfigError):
        run_preflight(cfg)
