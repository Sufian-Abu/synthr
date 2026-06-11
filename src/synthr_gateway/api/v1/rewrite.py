"""POST /v1/rewrite — transform text per an instruction."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.rewrite import RewriteRequest, rewrite
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/rewrite",
    summary="Rewrite text",
    description="Rewrites `text` per `instruction` (grammar, tone, length, style). Auth: `X-Project-Key` header.",
    responses=feature_responses("rewrite", {"text": "We were hoping you might be able to help us."}),
)
async def rewrite_route(
    body: RewriteRequest,
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
        "rewrite",
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
        run=lambda provider, model: rewrite(body, provider, model),
        guard_text=body.text,
    )
