"""Capture a screenshot of the running dashboard into docs/dashboard.png.

Usage:
    pip install playwright && playwright install chromium
    # with a Synthr gateway running on :8000 (ideally after a few requests so there's data):
    python scripts/capture_dashboard.py
"""

from __future__ import annotations

from pathlib import Path

from playwright.sync_api import sync_playwright

URL = "http://localhost:8000/dashboard"
OUT = Path(__file__).resolve().parents[1] / "docs" / "dashboard.png"


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={"width": 1100, "height": 900})
        page.goto(URL, wait_until="networkidle")
        page.wait_for_timeout(800)  # let HTMX fill in
        page.screenshot(path=str(OUT), full_page=True)
        browser.close()
    print(f"saved {OUT}")


if __name__ == "__main__":
    main()
