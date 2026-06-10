"""POST /v1/image — text-to-image generation."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.image import ImageRequest, generate_image
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/image",
    summary="Generate an image",
    description="Text-to-image generation. Backend-only by default (public/browser keys are blocked). Auth: `X-Project-Key` header.",
    responses=feature_responses("image", {"images": [{"b64": "iVBORw0KGgo…", "mime": "image/png"}]}),
)
async def image_route(
    body: ImageRequest,
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
        "image",
        request_payload=body.model_dump(),
        config=config,
        providers=providers,
        cache=cache,
        limiter=limiter,
        usage=usage,
        key=x_project_key,
        origin=origin,
        user_id=x_user_id,
        capability=Capability.IMAGE,
        run=lambda provider, model: generate_image(body, provider, model),
        guard_text=body.prompt,
    )
