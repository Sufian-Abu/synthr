"""Shared HTTP for provider adapters: POST JSON with retry on transient failures.

Retries 429 and 5xx (and network/timeout errors) with exponential backoff, honoring
a numeric Retry-After header when present. Every terminal failure is mapped to a typed
`SynthrError` (provider_timeout / provider_rate_limited / provider_error /
provider_invalid_response) so the runner can decide whether to fail over.
"""

from __future__ import annotations

import asyncio

import httpx

from ..core import errors

RETRYABLE_STATUS = {429, 500, 502, 503, 504}


def _retry_after(resp: httpx.Response | None) -> int | None:
    if resp is not None:
        ra = resp.headers.get("retry-after", "")
        if ra.isdigit():
            return int(ra)
    return None


def _delay(backoff: float, attempt: int, resp: httpx.Response | None = None) -> float:
    ra = _retry_after(resp)
    return float(ra) if ra is not None else backoff * (2**attempt)


async def post_json(
    url: str,
    *,
    json: dict,
    headers: dict | None = None,
    timeout: float = 60.0,
    retries: int = 3,
    backoff: float = 0.5,
) -> dict:
    """POST `json` and return the parsed response, retrying transient failures.

    Raises a typed `SynthrError` on any terminal failure.
    """
    headers = headers or {}
    for attempt in range(retries):
        is_last = attempt == retries - 1
        try:
            async with httpx.AsyncClient(timeout=timeout) as client:
                resp = await client.post(url, json=json, headers=headers)
        except httpx.TimeoutException as exc:
            if is_last:
                raise errors.provider_timeout() from exc
            await asyncio.sleep(_delay(backoff, attempt))
            continue
        except httpx.TransportError as exc:
            if is_last:
                raise errors.provider_error(f"Network error contacting provider: {exc}") from exc
            await asyncio.sleep(_delay(backoff, attempt))
            continue

        if resp.status_code in RETRYABLE_STATUS and not is_last:
            await asyncio.sleep(_delay(backoff, attempt, resp))
            continue

        # Terminal response — map status to a typed error or parse the body.
        status = resp.status_code
        if status == 429:
            raise errors.provider_rate_limited(retry_after=_retry_after(resp))
        if status >= 500:
            raise errors.provider_error(f"Provider returned HTTP {status}.")
        if status >= 400:
            detail = getattr(resp, "text", "") or ""
            raise errors.provider_error(f"Provider rejected the request (HTTP {status}). {detail[:200]}".strip())
        try:
            return resp.json()
        except ValueError as exc:
            raise errors.provider_invalid_response("Provider response was not valid JSON.") from exc

    raise RuntimeError("unreachable")  # loop always returns or raises
