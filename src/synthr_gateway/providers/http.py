"""Shared HTTP for provider adapters: POST JSON (with retry) and POST SSE (streaming).

Retries 429 and 5xx (and network/timeout errors) with exponential backoff, honoring a
numeric Retry-After header when present. Every terminal failure is mapped to a typed
`SynthrError`. Adapters may pass a `classify_error` callback to translate their provider's
own error *body* into a typed code; otherwise a generic status-based mapping is used.
"""

from __future__ import annotations

import asyncio
import base64
import json as jsonlib
from collections.abc import AsyncIterator, Callable

import httpx

from ..core import errors

RETRYABLE_STATUS = {429, 500, 502, 503, 504}

# (status, body_text, headers) -> a typed error, or None to fall back to generic mapping.
ErrorClassifier = Callable[[int, str, "httpx.Headers | dict"], "errors.SynthrError | None"]


def _retry_after(headers: httpx.Headers | dict | None) -> int | None:
    ra = (headers or {}).get("retry-after", "")
    return int(ra) if isinstance(ra, str) and ra.isdigit() else None


def _delay(backoff: float, attempt: int, headers: httpx.Headers | dict | None = None) -> float:
    ra = _retry_after(headers)
    return float(ra) if ra is not None else backoff * (2**attempt)


def _terminal_error(status: int, text: str, headers, classify_error: ErrorClassifier | None) -> errors.SynthrError:
    if classify_error:
        mapped = classify_error(status, text, headers)
        if mapped is not None:
            return mapped
    if status == 429:
        return errors.provider_rate_limited(retry_after=_retry_after(headers))
    if status >= 500:
        return errors.provider_error(f"Provider returned HTTP {status}.")
    return errors.provider_error(f"Provider rejected the request (HTTP {status}). {text[:200]}".strip())


async def post_json(
    url: str,
    *,
    json: dict,
    headers: dict | None = None,
    timeout: float = 60.0,
    retries: int = 3,
    backoff: float = 0.5,
    classify_error: ErrorClassifier | None = None,
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
            await asyncio.sleep(_delay(backoff, attempt, resp.headers))
            continue

        if resp.status_code >= 400:
            raise _terminal_error(resp.status_code, getattr(resp, "text", "") or "", resp.headers, classify_error)
        try:
            return resp.json()
        except ValueError as exc:
            raise errors.provider_invalid_response("Provider response was not valid JSON.") from exc

    raise RuntimeError("unreachable")  # loop always returns or raises


async def fetch_image(url: str, *, timeout: float = 30.0) -> tuple[str, str]:
    """Download an image and return (base64, mime-type)."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(url)
    except httpx.HTTPError as exc:
        raise errors.invalid_input(f"Could not fetch image_url: {exc}") from exc
    if resp.status_code >= 400:
        raise errors.invalid_input(f"Could not fetch image_url (HTTP {resp.status_code}).")
    mime = resp.headers.get("content-type", "image/png").split(";")[0].strip() or "image/png"
    return base64.b64encode(resp.content).decode(), mime


async def post_sse(
    url: str,
    *,
    json: dict,
    headers: dict | None = None,
    timeout: float = 120.0,
    classify_error: ErrorClassifier | None = None,
) -> AsyncIterator[dict]:
    """POST and yield parsed JSON objects from a Server-Sent-Events stream (`data:` lines).

    Stops on the `[DONE]` sentinel. Errors map to typed `SynthrError` (no retry on a stream).
    """
    hdrs = {**(headers or {}), "Accept": "text/event-stream"}
    async with httpx.AsyncClient(timeout=timeout) as client:
        async with client.stream("POST", url, json=json, headers=hdrs) as resp:
            if resp.status_code >= 400:
                body = (await resp.aread()).decode("utf-8", "replace")
                raise _terminal_error(resp.status_code, body, resp.headers, classify_error)
            async for raw in resp.aiter_lines():
                line = raw.strip()
                if not line or line.startswith(":"):  # blank or comment/keepalive
                    continue
                if line.startswith("data:"):
                    data = line[5:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        yield jsonlib.loads(data)
                    except ValueError:
                        continue
