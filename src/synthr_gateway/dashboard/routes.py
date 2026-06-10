"""Dashboard routes. `/dashboard` is the page; `/dashboard/stats` is the HTMX partial."""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Depends, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates

from ..api.deps import get_usage
from ..usage import UsageLog

templates = Jinja2Templates(directory=str(Path(__file__).parent / "templates"))
templates.env.filters["comma"] = lambda v: f"{int(v or 0):,}"  # 1234567 -> "1,234,567"
templates.env.filters["usd"] = lambda v: f"${float(v or 0):,.4f}"
router = APIRouter()


def _stats(usage: UsageLog) -> dict:
    return {
        "totals": usage.totals(),
        "by_feature": usage.by_feature(),
        "by_provider": usage.by_provider(),
        "recent": usage.recent(),
        "events": usage.recent_events(),
    }


@router.get("/dashboard", response_class=HTMLResponse)
async def dashboard(request: Request, usage: UsageLog = Depends(get_usage)) -> HTMLResponse:
    return templates.TemplateResponse(request, "index.html", _stats(usage))


@router.get("/dashboard/stats", response_class=HTMLResponse)
async def stats(request: Request, usage: UsageLog = Depends(get_usage)) -> HTMLResponse:
    return templates.TemplateResponse(request, "partials/stats.html", _stats(usage))
