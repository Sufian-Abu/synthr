"""Response examples for the feature routes, so ReDoc shows real payloads.

Every feature returns the same envelope: `{ "data": ..., "meta": {...} }`. These
helpers attach a success example plus the common auth/rate-limit error shapes.
"""

from __future__ import annotations

from typing import Any


def _ok(data: dict, feature: str, provider: str) -> dict:
    return {
        "data": data,
        "meta": {
            "feature": feature,
            "provider": provider,
            "cached": False,
            "request_id": "req_ab12cd34ef56",
            "usage": {"prompt_tokens": 64, "completion_tokens": 12},
        },
    }


def _err(code: str, message: str, **extra: Any) -> dict:
    return {"content": {"application/json": {"example": {"error": {"code": code, "message": message, **extra}}}}}


def feature_responses(feature: str, example_data: dict, *, provider: str = "gemini") -> dict:
    """OpenAPI `responses` for a feature route: 200 envelope + 401/429 errors."""
    return {
        200: {
            "description": "Success — unified response envelope.",
            "content": {"application/json": {"example": _ok(example_data, feature, provider)}},
        },
        401: {"description": "Missing or invalid project key.", **_err("invalid_key", "Invalid or unknown project key.")},
        429: {
            "description": "Rate limit exceeded.",
            **_err("rate_limited", "Rate limit exceeded.", retry_after_seconds=3600),
        },
    }
