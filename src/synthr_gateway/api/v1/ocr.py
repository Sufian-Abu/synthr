"""POST /v1/ocr — read the text in an image."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.ocr import OcrRequest, ocr
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..openapi import feature_responses
from ..runner import execute

router = APIRouter()


@router.post(
    "/ocr",
    summary="Read the text in an image",
    description="Extracts text from an `image` (base64/data-URI) or `image_url`. Auth: `X-Project-Key` header.",
    responses=feature_responses("ocr", {"text": "INVOICE 412\nAcme Corp\nTotal: $1,290.00"}),
)
async def ocr_route(
    body: OcrRequest,
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
        "ocr",
        request_payload=body.model_dump(),
        config=config,
        providers=providers,
        cache=cache,
        limiter=limiter,
        usage=usage,
        key=x_project_key,
        origin=origin,
        user_id=x_user_id,
        capability=Capability.VISION,
        run=lambda provider, model: ocr(body, provider, model),
        guard_text=None,
    )
