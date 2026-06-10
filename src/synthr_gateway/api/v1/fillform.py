"""POST /v1/fillForm — schema-constrained form autofill."""

from __future__ import annotations

from fastapi import APIRouter, Depends, Header

from ...cache import CacheManager
from ...config import Config
from ...features.fillform import FillFormRequest, fill_form
from ...providers import Capability, Provider
from ...ratelimit import RateLimiter
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..runner import execute

router = APIRouter()


@router.post(
    "/fillForm",
    summary="Auto-fill a form from free text",
    description=(
        "Give your form's **fields** (name + type, optional `options`) and a free-text "
        "**context**. Returns a value for each field. Fields not found in the context come "
        "back `null` and are listed in `unfilled` — it never guesses. Auth: `X-Project-Key` header."
    ),
)
async def fill_form_route(
    body: FillFormRequest,
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
        "fillForm",
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
        run=lambda provider, model: fill_form(body, provider, model),
        guard_text=str(body.context),
    )
