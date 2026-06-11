"""POST /v1/moderate — content-safety classification."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.moderate import ModerateRequest, moderate
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/moderate",
    summary="Flag unsafe content",
    description="Classifies `text` for safety. Returns `flagged`, `categories`, and a `reason`. Auth: `X-Project-Key` header.",
    responses=feature_responses(
        "moderate",
        {"flagged": True, "categories": ["harassment", "violence"], "reason": "Threatening language directed at a person."},
    ),
)
async def moderate_route(
    body: ModerateRequest,
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
        "moderate",
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
        run=lambda provider, model: moderate(body, provider, model),
        guard_text=body.text,
    )
