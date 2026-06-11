"""Background jobs — submit any feature, poll for the result.

    POST /v1/jobs        { "feature": "image", "payload": { ... } }  -> { id, status }
    GET  /v1/jobs/{id}                                              -> { status, result | error }

For slow features (image generation, background removal) so the caller doesn't hold a
connection open. The job runs the same pipeline (auth, guardrails, limits, cache, fallback,
cost) on a worker thread.
"""

from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse
from pydantic import BaseModel

from ...cache import CacheManager
from ...config import Config
from ...core import errors
from ...features.dispatch import DISPATCH
from ...jobs import JobManager, JobStore
from ...providers import Provider
from ...ratelimit import RateLimiter
from ...security import authenticate, authorize_feature
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_jobs, get_jobs_store, get_limiter, get_providers, get_usage
from ..runner import execute

router = APIRouter()


class JobRequest(BaseModel):
    feature: str
    payload: dict = {}


def _err(exc: errors.SynthrError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content={"error": {"code": exc.code, "message": exc.message}})


@router.post("/jobs", summary="Submit a feature as a background job", tags=["features"])
async def submit_job(
    body: JobRequest,
    config: Config = Depends(get_config),
    providers: dict[str, Provider] = Depends(get_providers),
    cache: CacheManager = Depends(get_cache),
    limiter: RateLimiter = Depends(get_limiter),
    usage: UsageLog = Depends(get_usage),
    jobs_store: JobStore = Depends(get_jobs_store),
    jobs: JobManager = Depends(get_jobs),
    x_project_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    origin: str | None = Header(default=None),
):
    spec = DISPATCH.get(body.feature)
    if spec is None:
        return _err(errors.invalid_input(f"Unknown feature {body.feature!r}."))
    feature_cfg = config.features.get(body.feature)
    if feature_cfg is None:
        return _err(errors.invalid_input(f"Feature {body.feature!r} is not configured."))

    try:
        request_model = spec.model.model_validate(body.payload)
        auth = authenticate(config, x_project_key, origin)
        authorize_feature(auth, body.feature, feature_cfg)
    except errors.SynthrError as exc:
        return _err(exc)
    except Exception as exc:  # noqa: BLE001 — pydantic validation errors on the payload
        return _err(errors.invalid_input(f"Invalid payload for {body.feature!r}: {exc}"))

    job_id = "job_" + uuid.uuid4().hex[:16]
    subject = x_user_id or auth.key_id
    jobs_store.create(job_id, project=auth.project_id, subject=subject, feature=body.feature)

    async def _coro() -> dict:
        envelope = await execute(
            body.feature,
            request_payload=request_model.model_dump(),
            config=config,
            providers=providers,
            cache=cache,
            limiter=limiter,
            usage=usage,
            key=x_project_key,
            origin=origin,
            user_id=x_user_id,
            capability=spec.capability,
            run=lambda provider, model: spec.service(request_model, provider, model),
            guard_text=spec.guard(request_model),
        )
        return envelope["data"]

    jobs.submit(job_id, _coro)
    return {"id": job_id, "status": "queued", "feature": body.feature}


@router.get("/jobs/{job_id}", summary="Get a background job's status / result", tags=["features"])
async def get_job(
    job_id: str,
    config: Config = Depends(get_config),
    jobs_store: JobStore = Depends(get_jobs_store),
    x_project_key: str | None = Header(default=None),
    origin: str | None = Header(default=None),
):
    try:
        auth = authenticate(config, x_project_key, origin)
    except errors.SynthrError as exc:
        return _err(exc)

    job = jobs_store.get(job_id)
    if job is None or job.get("project") != auth.project_id:
        return _err(errors.not_found(f"Job {job_id!r} not found."))
    job.pop("project", None)  # don't echo internal project id
    return job
