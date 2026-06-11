"""POST /v1/extract — pull a list of structured records from text."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.extract import ExtractRequest, extract
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/extract",
    summary="Extract structured data from text",
    description=(
        "Two modes: pass a `schema` (`{field: type}`) to get **one** structured record, or "
        "`fields` (a list of field defs) to get a **list** of records under `items`. "
        "Auth: `X-Project-Key` header."
    ),
    responses=feature_responses("extract", {"amount": 1290.0, "vendor": "Acme Corp", "date": "2026-02-01"}),
)
async def extract_route(
    body: ExtractRequest,
    config: Config = Depends(get_config),
    providers: dict[str, Provider] = Depends(get_providers),
    cache: CacheManager = Depends(get_cache),
    limiter: RateLimiter = Depends(get_limiter),
    usage: UsageLog = Depends(get_usage),
    x_project_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    origin: str | None = Header(default=None),
) -> dict:
    return await execute(
        "extract",
        request_payload=body.model_dump(),
        config=config,
        providers=providers,
        cache=cache,
        limiter=limiter,
        usage=usage,
        key=x_project_key,
        origin=origin,
        user_id=x_user_id,
        capability=Capability.TEXT,
        run=lambda provider, model: extract(body, provider, model),
        guard_text=body.text,
    )
