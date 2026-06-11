"""classify / extract / moderate — schema-constrained text features through the pipeline."""

from __future__ import annotations

from fastapi.testclient import TestClient

SECRET = {"X-Project-Key": "sk_proj_test"}


def test_classify_shape(client: TestClient) -> None:
    r = client.post("/v1/classify", headers=SECRET, json={"text": "it crashes", "labels": ["bug", "praise"]})
    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"label", "confidence"}


def test_classify_needs_two_labels(client: TestClient) -> None:
    r = client.post("/v1/classify", headers=SECRET, json={"text": "x", "labels": ["only-one"]})
    assert r.status_code == 422  # validation: min 2 labels


def test_extract_schema_returns_record(client: TestClient) -> None:
    r = client.post(
        "/v1/extract",
        headers=SECRET,
        json={"text": "Acme billed $1290 on 2026-02-01", "schema": {"amount": "number", "vendor": "string"}},
    )
    assert r.status_code == 200
    assert set(r.json()["data"]) == {"amount", "vendor"}  # one record, the schema's fields


def test_extract_fields_returns_items_list(client: TestClient) -> None:
    r = client.post(
        "/v1/extract",
        headers=SECRET,
        json={"fields": [{"name": "item", "type": "string"}, {"name": "qty", "type": "integer"}], "text": "2x Coffee"},
    )
    assert r.status_code == 200
    assert isinstance(r.json()["data"]["items"], list)


def test_extract_requires_schema_or_fields(client: TestClient) -> None:
    r = client.post("/v1/extract", headers=SECRET, json={"text": "nothing to go on"})
    assert r.status_code == 422


def test_moderate_shape(client: TestClient) -> None:
    r = client.post("/v1/moderate", headers=SECRET, json={"text": "have a nice day"})
    assert r.status_code == 200
    data = r.json()["data"]
    assert set(data) == {"flagged", "categories", "reason"}
    assert isinstance(data["flagged"], bool)
    assert isinstance(data["categories"], list)
