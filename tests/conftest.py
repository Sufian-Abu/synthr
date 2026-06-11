"""Shared fixtures. Tests run against the mock provider — no network, no keys."""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from synthr_gateway.app import create_app

CONFIG = """
gateway:
  secret: test-secret
  db_path: ":memory:"
providers:
  mock: { kind: mock }
features:
  fillForm:
    provider: mock
    frontend_safe: true
    cache: { enabled: true, mode: exact, ttl_minutes: 60 }
  image:
    provider: mock
    frontend_safe: false
    cache: { enabled: true, mode: exact, ttl_minutes: 60 }
  removeBackground:
    provider: mock
    frontend_safe: true
    cache: { enabled: true, mode: exact, ttl_minutes: 60 }
  summarize:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  translate:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  chat:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  generate:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  rewrite:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  seo:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  classify:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  extract:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  moderate:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
  embed:
    provider: mock
    frontend_safe: true
    cache: { enabled: false }
projects:
  demo:
    keys:
      - { id: sk_proj_test, type: secret }
      - { id: pk_proj_test, type: public, allowed_origins: ["http://localhost:3000"] }
"""


@pytest.fixture()
def client(tmp_path: Path) -> TestClient:
    cfg = tmp_path / "synthr.config.yaml"
    cfg.write_text(CONFIG)
    return TestClient(create_app(cfg))


@pytest.fixture()
def fillform_body() -> dict:
    return {
        "fields": [
            {"name": "brand", "type": "string"},
            {"name": "size", "type": "number"},
            {"name": "color", "type": "string", "options": ["red", "blue"]},
        ],
        "context": "Nike Air Max, red, size 10",
    }
