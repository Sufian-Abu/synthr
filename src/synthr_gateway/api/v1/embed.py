"""POST /v1/embed — text(s) to embedding vector(s)."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.embed import EmbedRequest, embed
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/embed",
    summary="Embed text into vectors",
    description="Returns an embedding vector per input string (one string or a batch). Auth: `X-Project-Key` header.",
    responses=feature_responses("embed", {"model": "text-embedding-004", "dimensions": 768, "vectors": [[0.01, -0.02, "…"]]}),
)
async def embed_route(
    body: EmbedRequest,
    config: Config = Depends(get_config),
    providers: dict[str, Provider] = Depends(get_providers),
    cache: CacheManager = Depends(get_cache),
    limiter: RateLimiter = Depends(get_limiter),
    usage: UsageLog = Depends(get_usage),
    x_project_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    origin: str | None = Header(default=None),
) -> dict:
    guard = body.input if isinstance(body.input, str) else " ".join(body.input)
    return await execute(
        "embed",
        request_payload=body.model_dump(),
        config=config,
        providers=providers,
        cache=cache,
        limiter=limiter,
        usage=usage,
        key=x_project_key,
        origin=origin,
        user_id=x_user_id,
        capability=Capability.EMBED,
        run=lambda provider, model: embed(body, provider, model),
        guard_text=guard,
    )
