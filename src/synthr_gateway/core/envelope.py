"""Unified response envelope (SPEC.md §4). Every feature returns the same shape."""

from __future__ import annotations

from .errors import SynthrError


def success(
    data: dict,
    *,
    feature: str,
    provider: str,
    cached: bool,
    request_id: str,
    usage: dict | None = None,
) -> dict:
    meta: dict = {"feature": feature, "provider": provider, "cached": cached, "request_id": request_id}
    if usage is not None:
        meta["usage"] = usage
    return {"data": data, "meta": meta}


def error_payload(err: SynthrError) -> dict:
    payload: dict = {"code": err.code, "message": err.message}
    if err.retry_after is not None:
        payload["retry_after_seconds"] = err.retry_after
    return {"error": payload}
