"""POST /v1/generate — freeform prompt to text."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.generate import GenerateRequest, generate
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/generate",
    summary="Generate freeform text",
    description="Freeform prompt to text — the escape hatch when no named feature fits. Auth: `X-Project-Key` header.",
    responses=feature_responses("generate", {"text": "Plug-and-play AI for every project."}),
)
async def generate_route(
    body: GenerateRequest,
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
        "generate",
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
        run=lambda provider, model: generate(body, provider, model),
        guard_text=body.prompt,
    )
