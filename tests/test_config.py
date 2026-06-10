"""Config loading surfaces friendly, field-level errors (not raw tracebacks)."""

from __future__ import annotations

from pathlib import Path

import pytest

from synthr_gateway.config import ConfigError, load_config


def _write(tmp_path: Path, text: str) -> Path:
    cfg = tmp_path / "c.yaml"
    cfg.write_text(text)
    return cfg


def test_missing_file_is_friendly(tmp_path: Path) -> None:
    with pytest.raises(ConfigError) as exc:
        load_config(tmp_path / "nope.yaml")
    assert "not found" in str(exc.value)


def test_malformed_yaml_is_friendly(tmp_path: Path) -> None:
    cfg = _write(tmp_path, "providers: [1, 2\n")  # unterminated flow sequence
    with pytest.raises(ConfigError) as exc:
        load_config(cfg)
    assert "valid YAML" in str(exc.value)


def test_unknown_provider_reference(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path,
        "providers:\n  mock: { kind: mock }\nfeatures:\n  summarize:\n    provider: gemini\n",
    )
    with pytest.raises(ConfigError) as exc:
        load_config(cfg)
    assert "gemini" in str(exc.value)


def test_unknown_fallback_provider(tmp_path: Path) -> None:
    cfg = _write(
        tmp_path,
        "providers:\n  mock: { kind: mock }\n"
        "features:\n  summarize:\n    provider: mock\n    fallback: { provider: nope }\n",
    )
    with pytest.raises(ConfigError) as exc:
        load_config(cfg)
    assert "nope" in str(exc.value)


def test_invalid_field_type_names_the_field(tmp_path: Path) -> None:
    cfg = _write(tmp_path, "gateway:\n  port: not-a-number\nproviders:\n  mock: { kind: mock }\n")
    with pytest.raises(ConfigError) as exc:
        load_config(cfg)
    assert "port" in str(exc.value)
