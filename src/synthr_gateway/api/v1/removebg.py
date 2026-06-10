"""POST /v1/removeBackground — strip an image background (non-LLM provider)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.removebg import RemoveBackgroundRequest, remove_background
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..runner import execute

router = APIRouter()


@router.post(
    "/removeBackground",
    summary="Remove an image background",
    description=(
        "Returns a transparent PNG with the background removed. Send `image` (base64/data-URI) "
        "or `image_url`. Runs locally via `rembg` (needs the `vision` extra). Auth: `X-Project-Key` header."
    ),
)
async def remove_background_route(
    body: RemoveBackgroundRequest,
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
        "removeBackground",
        request_payload=body.model_dump(),
        config=config,
        providers=providers,
        cache=cache,
        limiter=limiter,
        usage=usage,
        key=x_project_key,
        origin=origin,
        user_id=x_user_id,
        capability=Capability.REMOVE_BACKGROUND,
        run=lambda provider, model: remove_background(body, provider, model),
    )
