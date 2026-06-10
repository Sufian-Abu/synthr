"""Shared HTTP for provider adapters: POST JSON with retry on transient failures.

Retries 429 and 5xx (and network/timeout errors) with exponential backoff, honoring
a numeric Retry-After header when present. Non-retryable 4xx raise immediately.
"""

from __future__ import annotations

import asyncio

import httpx

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _delay(backoff: float, attempt: int, resp: httpx.Response | None = None) -> float:
    if resp is not None:
        retry_after = resp.headers.get("retry-after", "")
        if retry_after.isdigit():
            return float(retry_after)
    return backoff * (2**attempt)


async def post_json(
    url: str,
    *,
    json: dict,
    headers: dict | None = None,
    timeout: float = 60.0,
    retries: int = 3,
    backoff: float = 0.5,
) -> dict:
    """POST `json` and return the parsed response, retrying transient failures."""
    headers = headers or {}
    for attempt in range(retries):
        is_last = attempt == retries - 1
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=json, headers=headers)
        except (httpx.TimeoutException, httpx.TransportError):
            if is_last:
                raise
            await asyncio.sleep(_delay(backoff, attempt))
            continue

        if resp.status_code in RETRYABLE_STATUS and not is_last:
            await asyncio.sleep(_delay(backoff, attempt, resp))
            continue

        resp.raise_for_status()
        return resp.json()

    raise RuntimeError("unreachable")  # loop always returns or raises
