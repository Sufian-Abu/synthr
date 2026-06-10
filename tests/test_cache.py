"""Exact-match cache behaviour (SPEC.md §5)."""

from __future__ import annotations

from fastapi.testclient import TestClient

KEY = {"X-Project-Key": "sk_proj_test"}


def test_second_identical_call_is_a_cache_hit(client: TestClient, fillform_body: dict) -> None:
    assert client.post("/v1/fillForm", headers=KEY, json=fillform_body).json()["meta"]["cached"] is False
    assert client.post("/v1/fillForm", headers=KEY, json=fillform_body).json()["meta"]["cached"] is True


def test_different_input_is_a_miss(client: TestClient, fillform_body: dict) -> None:
    client.post("/v1/fillForm", headers=KEY, json=fillform_body)
    other = {**fillform_body, "context": "Adidas Ultraboost, blue, size 9"}
    assert client.post("/v1/fillForm", headers=KEY, json=other).json()["meta"]["cached"] is False
