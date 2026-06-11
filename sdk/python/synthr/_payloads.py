"""Build request bodies + unwrap the response envelope. Shared by sync and async."""

from __future__ import annotations

from typing import Any

import httpx

from .errors import SynthrError


def fill_form(fields: list[dict], context: Any, locale: str | None) -> tuple[str, dict]:
    body: dict = {"fields": fields, "context": context}
    if locale:
        body["locale"] = locale
    return "fillForm", body


def summarize(text: str, max_words: int | None) -> tuple[str, dict]:
    body: dict = {"text": text}
    if max_words is not None:
        body["max_words"] = max_words
    return "summarize", body


def translate(text: str, target_lang: str) -> tuple[str, dict]:
    return "translate", {"text": text, "target_lang": target_lang}


def image(prompt: str, size: str, n: int) -> tuple[str, dict]:
    return "image", {"prompt": prompt, "size": size, "n": n}


def remove_background(image_b64: str | None, image_url: str | None) -> tuple[str, dict]:
    body: dict = {}
    if image_b64:
        body["image"] = image_b64
    if image_url:
        body["image_url"] = image_url
    return "removeBackground", body


def generate(prompt: str, max_words: int | None) -> tuple[str, dict]:
    body: dict = {"prompt": prompt}
    if max_words is not None:
        body["max_words"] = max_words
    return "generate", body


def rewrite(text: str, instruction: str | None) -> tuple[str, dict]:
    body: dict = {"text": text}
    if instruction:
        body["instruction"] = instruction
    return "rewrite", body


def seo(content: str) -> tuple[str, dict]:
    return "seo", {"content": content}


def classify(text: str, labels: list[str]) -> tuple[str, dict]:
    return "classify", {"text": text, "labels": labels}


def extract(text: str, schema: dict | None, fields: list[dict] | None) -> tuple[str, dict]:
    body: dict = {"text": text}
    if schema is not None:
        body["schema"] = schema
    if fields is not None:
        body["fields"] = fields
    return "extract", body


def moderate(text: str) -> tuple[str, dict]:
    return "moderate", {"text": text}


def ocr(image_b64: str | None, image_url: str | None) -> tuple[str, dict]:
    body: dict = {}
    if image_b64:
        body["image"] = image_b64
    if image_url:
        body["image_url"] = image_url
    return "ocr", body


def embed(inputs: str | list[str]) -> tuple[str, dict]:
    return "embed", {"input": inputs}


def unwrap(resp: httpx.Response) -> dict:
    """Return the `data` payload, or raise SynthrError on an error envelope."""
    if resp.status_code >= 400:
        try:
            err = resp.json().get("error", {})
        except Exception:  # noqa: BLE001 — non-JSON error body
            err = {}
        raise SynthrError(
            err.get("code", "http_error"),
            err.get("message", resp.text[:200]),
            resp.status_code,
            err.get("retry_after_seconds"),
        )
    return resp.json()["data"]
