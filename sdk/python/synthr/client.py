"""Sync (`AI`) and async (`AsyncAI`) clients. Each method returns the `data` payload."""

from __future__ import annotations

import os
from typing import Any

import httpx

from . import _payloads as p

DEFAULT_URL = "http://localhost:8000"


def _resolve(key: str | None, url: str | None) -> tuple[str | None, str]:
    key = key or os.environ.get("SYNTHR_KEY")
    url = (url or os.environ.get("SYNTHR_URL") or DEFAULT_URL).rstrip("/")
    return key, url


class AI:
    """Synchronous client."""

    def __init__(
        self,
        key: str | None = None,
        *,
        url: str | None = None,
        user_id: str | None = None,
        timeout: float = 60.0,
        http_client: httpx.Client | None = None,
    ) -> None:
        self.key, self.url = _resolve(key, url)
        self.user_id = user_id
        self._owns = http_client is None
        self._client = http_client or httpx.Client(base_url=self.url, timeout=timeout)

    def _headers(self) -> dict:
        headers = {}
        if self.key:
            headers["X-Project-Key"] = self.key
        if self.user_id:
            headers["X-User-Id"] = self.user_id
        return headers

    def _call(self, feature: str, body: dict) -> dict:
        return p.unwrap(self._client.post(f"/v1/{feature}", json=body, headers=self._headers()))

    def fill_form(self, fields: list[dict], context: Any, locale: str | None = None) -> dict:
        return self._call(*p.fill_form(fields, context, locale))

    def summarize(self, text: str, max_words: int | None = None) -> dict:
        return self._call(*p.summarize(text, max_words))

    def translate(self, text: str, target_lang: str) -> dict:
        return self._call(*p.translate(text, target_lang))

    def image(self, prompt: str, size: str = "1024x1024", n: int = 1) -> dict:
        return self._call(*p.image(prompt, size, n))

    def remove_background(self, image: str | None = None, image_url: str | None = None) -> dict:
        return self._call(*p.remove_background(image, image_url))

    def generate(self, prompt: str, max_words: int | None = None) -> dict:
        return self._call(*p.generate(prompt, max_words))

    def rewrite(self, text: str, instruction: str | None = None) -> dict:
        return self._call(*p.rewrite(text, instruction))

    def seo(self, content: str) -> dict:
        return self._call(*p.seo(content))

    def classify(self, text: str, labels: list[str]) -> dict:
        return self._call(*p.classify(text, labels))

    def extract(self, text: str, schema: dict | None = None, fields: list[dict] | None = None) -> dict:
        return self._call(*p.extract(text, schema, fields))

    def moderate(self, text: str) -> dict:
        return self._call(*p.moderate(text))

    def embed(self, inputs: str | list[str]) -> dict:
        return self._call(*p.embed(inputs))

    def run(self, feature: str, payload: dict) -> dict:
        """Escape hatch for any feature, including custom ones."""
        return self._call(feature, payload)

    def close(self) -> None:
        if self._owns:
            self._client.close()

    def __enter__(self) -> "AI":
        return self

    def __exit__(self, *_: object) -> None:
        self.close()


class AsyncAI:
    """Asynchronous client (same surface, awaitable)."""

    def __init__(
        self,
        key: str | None = None,
        *,
        url: str | None = None,
        user_id: str | None = None,
        timeout: float = 60.0,
        http_client: httpx.AsyncClient | None = None,
    ) -> None:
        self.key, self.url = _resolve(key, url)
        self.user_id = user_id
        self._owns = http_client is None
        self._client = http_client or httpx.AsyncClient(base_url=self.url, timeout=timeout)

    def _headers(self) -> dict:
        headers = {}
        if self.key:
            headers["X-Project-Key"] = self.key
        if self.user_id:
            headers["X-User-Id"] = self.user_id
        return headers

    async def _call(self, feature: str, body: dict) -> dict:
        return p.unwrap(await self._client.post(f"/v1/{feature}", json=body, headers=self._headers()))

    async def fill_form(self, fields: list[dict], context: Any, locale: str | None = None) -> dict:
        return await self._call(*p.fill_form(fields, context, locale))

    async def summarize(self, text: str, max_words: int | None = None) -> dict:
        return await self._call(*p.summarize(text, max_words))

    async def translate(self, text: str, target_lang: str) -> dict:
        return await self._call(*p.translate(text, target_lang))

    async def image(self, prompt: str, size: str = "1024x1024", n: int = 1) -> dict:
        return await self._call(*p.image(prompt, size, n))

    async def remove_background(self, image: str | None = None, image_url: str | None = None) -> dict:
        return await self._call(*p.remove_background(image, image_url))

    async def generate(self, prompt: str, max_words: int | None = None) -> dict:
        return await self._call(*p.generate(prompt, max_words))

    async def rewrite(self, text: str, instruction: str | None = None) -> dict:
        return await self._call(*p.rewrite(text, instruction))

    async def seo(self, content: str) -> dict:
        return await self._call(*p.seo(content))

    async def classify(self, text: str, labels: list[str]) -> dict:
        return await self._call(*p.classify(text, labels))

    async def extract(self, text: str, schema: dict | None = None, fields: list[dict] | None = None) -> dict:
        return await self._call(*p.extract(text, schema, fields))

    async def moderate(self, text: str) -> dict:
        return await self._call(*p.moderate(text))

    async def embed(self, inputs: str | list[str]) -> dict:
        return await self._call(*p.embed(inputs))

    async def run(self, feature: str, payload: dict) -> dict:
        return await self._call(feature, payload)

    async def aclose(self) -> None:
        if self._owns:
            await self._client.aclose()

    async def __aenter__(self) -> "AsyncAI":
        return self

    async def __aexit__(self, *_: object) -> None:
        await self.aclose()
