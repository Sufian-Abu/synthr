"""Hashed keys, revoke, expiry, and scopes (Track 3 auth hardening)."""

from __future__ import annotations

import hashlib
from pathlib import Path

from fastapi.testclient import TestClient

from synthr_gateway.app import create_app

BODY = {"text": "hello world"}


def _sha256(s: str) -> str:
    return hashlib.sha256(s.encode()).hexdigest()


def _app(tmp_path: Path, keys_yaml: str, *, features: str = "") -> TestClient:
    extra = features or "  summarize:\n    provider: mock\n    frontend_safe: true\n    cache: { enabled: false }\n"
    cfg = tmp_path / "c.yaml"
    cfg.write_text(
        "gateway: { secret: t, db_path: ':memory:' }\n"
        "providers:\n  mock: { kind: mock }\n"
        f"features:\n{extra}"
        f"projects:\n  demo:\n    keys:\n{keys_yaml}"
    )
    return TestClient(create_app(cfg))


def test_hashed_key_authenticates(tmp_path: Path) -> None:
    key = "sk_proj_hashed_example"
    client = _app(tmp_path, f"      - type: secret\n        hash: {_sha256(key)}\n")
    r = client.post("/v1/summarize", headers={"X-Project-Key": key}, json=BODY)
    assert r.status_code == 200


def test_wrong_key_is_invalid(tmp_path: Path) -> None:
    client = _app(tmp_path, f"      - type: secret\n        hash: {_sha256('sk_proj_right')}\n")
    r = client.post("/v1/summarize", headers={"X-Project-Key": "sk_proj_wrong"}, json=BODY)
    assert r.status_code == 401 and r.json()["error"]["code"] == "invalid_key"


def test_revoked_key_rejected(tmp_path: Path) -> None:
    client = _app(tmp_path, "      - { type: secret, id: sk_proj_dead, revoked: true }\n")
    r = client.post("/v1/summarize", headers={"X-Project-Key": "sk_proj_dead"}, json=BODY)
    assert r.status_code == 403 and r.json()["error"]["code"] == "key_revoked"


def test_expired_key_rejected(tmp_path: Path) -> None:
    client = _app(tmp_path, '      - { type: secret, id: sk_proj_old, expires: "2000-01-01" }\n')
    r = client.post("/v1/summarize", headers={"X-Project-Key": "sk_proj_old"}, json=BODY)
    assert r.status_code == 401 and r.json()["error"]["code"] == "key_expired"


def test_future_expiry_still_valid(tmp_path: Path) -> None:
    client = _app(tmp_path, '      - { type: secret, id: sk_proj_fresh, expires: "2999-01-01" }\n')
    r = client.post("/v1/summarize", headers={"X-Project-Key": "sk_proj_fresh"}, json=BODY)
    assert r.status_code == 200


def test_scopes_restrict_features(tmp_path: Path) -> None:
    features = (
        "  summarize:\n    provider: mock\n    frontend_safe: true\n    cache: { enabled: false }\n"
        "  translate:\n    provider: mock\n    frontend_safe: true\n    cache: { enabled: false }\n"
    )
    keys = '      - { type: secret, id: sk_proj_scoped, scopes: ["summarize"] }\n'
    client = _app(tmp_path, keys, features=features)
    headers = {"X-Project-Key": "sk_proj_scoped"}
    assert client.post("/v1/summarize", headers=headers, json=BODY).status_code == 200
    blocked = client.post("/v1/translate", headers=headers, json={"text": "hi", "target_lang": "Spanish"})
    assert blocked.status_code == 403 and blocked.json()["error"]["code"] == "feature_not_allowed"
