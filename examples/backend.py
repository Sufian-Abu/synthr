"""Backend usage (Python). Until the pip SDK lands, it's a thin httpx call."""

from __future__ import annotations

import asyncio
import os

import httpx

BASE = os.environ.get("SYNTHR_URL", "http://localhost:8000")
KEY = os.environ.get("SYNTHR_KEY", "sk_proj_demo_secret")


async def call(feature: str, payload: dict) -> dict:
    async with httpx.AsyncClient(timeout=60) as client:
        resp = await client.post(
            f"{BASE}/v1/{feature}", json=payload, headers={"X-Project-Key": KEY, "X-User-Id": "backend-demo"}
        )
        resp.raise_for_status()
        return resp.json()


async def main() -> None:
    form = await call(
        "fillForm",
        {
            "fields": [
                {"name": "brand", "type": "string"},
                {"name": "size", "type": "number"},
                {"name": "color", "type": "string", "options": ["red", "blue", "black"]},
            ],
            "context": "Nike Air Max, red, size 10",
        },
    )
    print("fillForm  ->", form["data"]["values"], "| provider:", form["meta"]["provider"])

    summary = await call("summarize", {"text": "Synthr gives every project ready-made AI behind one SDK.", "max_words": 10})
    print("summarize ->", summary["data"]["summary"])

    tr = await call("translate", {"text": "Good morning", "target_lang": "French"})
    print("translate ->", tr["data"]["translation"])


if __name__ == "__main__":
    asyncio.run(main())
