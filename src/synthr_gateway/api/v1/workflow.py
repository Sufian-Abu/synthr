"""POST /v1/workflow — chain features together.

    { "steps": [ {"feature": "extract", "with": {...}},
                 {"feature": "summarize", "with": {"text": "${0.vendor} ..."}} ],
      "webhook": "https://..."  // optional }

Each step runs a feature through the full pipeline (auth, guardrails, limits, cache,
fallback, cost). Later steps reference earlier outputs with `${N.key}`. Without a webhook
the workflow runs inline and returns every step's output; with one it runs as a background
job and POSTs the final result to the URL.
"""

from __future__ import annotations

import re
import uuid
from functools import partial

import httpx
from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse

from ...cache import CacheManager
from ...config import Config
from ...core import errors
from ...features.dispatch import DISPATCH
from ...features.workflow import WorkflowRequest
from ...jobs import JobManager, JobStore
from ...providers import Provider
from ...ratelimit import RateLimiter
from ...security import authenticate
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_jobs, get_jobs_store, get_limiter, get_providers, get_usage
from ..runner import execute

router = APIRouter()

_PLACEHOLDER = re.compile(r"\$\{(\d+)\.([a-zA-Z0-9_]+)\}")


def _err(exc: errors.SynthrError) -> JSONResponse:
    return JSONResponse(status_code=exc.http_status, content={"error": {"code": exc.code, "message": exc.message}})


def _lookup(outputs: list[dict], idx: int, key: str):
    if idx >= len(outputs):
        raise errors.invalid_input(f"workflow references ${{{idx}.{key}}}, but step {idx} hasn't run yet")
    out = outputs[idx]
    if not isinstance(out, dict) or key not in out:
        raise errors.invalid_input(f"workflow step {idx} has no output field {key!r}")
    return out[key]


def _resolve(value, outputs: list[dict]):
    """Substitute ${N.key} placeholders from prior step outputs."""
    if isinstance(value, str):
        whole = _PLACEHOLDER.fullmatch(value.strip())
        if whole:  # the whole value is one reference — keep its real type (number, list, …)
            return _lookup(outputs, int(whole.group(1)), whole.group(2))
        return _PLACEHOLDER.sub(lambda m: str(_lookup(outputs, int(m.group(1)), m.group(2))), value)
    if isinstance(value, dict):
        return {k: _resolve(v, outputs) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, outputs) for v in value]
    return value


async def _run_workflow(body: WorkflowRequest, *, config, providers, cache, limiter, usage, key, origin, user_id) -> dict:
    outputs: list[dict] = []
    steps: list[dict] = []
    for i, step in enumerate(body.steps):
        spec = DISPATCH.get(step.feature)
        if spec is None:
            raise errors.invalid_input(f"unknown feature {step.feature!r} in step {i}")
        if config.features.get(step.feature) is None:
            raise errors.invalid_input(f"feature {step.feature!r} (step {i}) is not configured")
        payload = _resolve(step.with_, outputs)
        try:
            req = spec.model.model_validate(payload)
        except Exception as exc:  # noqa: BLE001 — pydantic validation on the resolved payload
            raise errors.invalid_input(f"step {i} ({step.feature}): invalid payload: {exc}") from exc

        envelope = await execute(
            step.feature,
            request_payload=req.model_dump(),
            config=config,
            providers=providers,
            cache=cache,
            limiter=limiter,
            usage=usage,
            key=key,
            origin=origin,
            user_id=user_id,
            capability=spec.capability,
            run=partial(spec.service, req),  # -> service(req, provider, model)
            guard_text=spec.guard(req),
        )
        outputs.append(envelope["data"])
        steps.append({"feature": step.feature, "data": envelope["data"]})

    return {"steps": steps, "result": outputs[-1] if outputs else None}


@router.post("/workflow", summary="Run a chain of features", tags=["features"])
async def workflow_route(
    body: WorkflowRequest,
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
    try:
        auth = authenticate(config, x_project_key, origin)
    except errors.SynthrError as exc:
        return _err(exc)

    deps = dict(
        config=config, providers=providers, cache=cache, limiter=limiter, usage=usage,
        key=x_project_key, origin=origin, user_id=x_user_id,
    )

    if body.webhook:
        webhook_url = body.webhook
        job_id = "job_" + uuid.uuid4().hex[:16]
        jobs_store.create(job_id, project=auth.project_id, subject=x_user_id or auth.key_id, feature="workflow")

        async def _coro() -> dict:
            result = await _run_workflow(body, **deps)
            try:  # best-effort delivery
                async with httpx.AsyncClient(timeout=10) as client:
                    await client.post(webhook_url, json=result)
            except Exception:  # noqa: BLE001
                pass
            return result

        jobs.submit(job_id, _coro)
        return {"id": job_id, "status": "queued", "feature": "workflow"}

    try:
        result = await _run_workflow(body, **deps)
    except errors.SynthrError as exc:
        return _err(exc)
    return {"data": result}
