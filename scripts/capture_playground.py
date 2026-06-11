"""Capture a screenshot of the Next.js playground into docs/playground.png.

Usage:
    pip install playwright && playwright install chromium
    # with the gateway on :8000 and the playground on :3000 (cd examples/nextjs && npm run dev):
    python scripts/capture_playground.py
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:3000"
OUT = Path(__file__).resolve().parents[1] / "docs" / "playground.png"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1200, "height": 1000}, device_scale_factor=2)
        page.goto(URL, wait_until="networkidle")
        # Fill the hero card so the screenshot shows a real result.
        try:
            page.get_by_text("Autofill the form").click()
            page.wait_for_timeout(2500)
        except Exception:  # noqa: BLE001 — best-effort; still capture the page
            pass
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
