"""Shared request lifecycle for every feature route.

auth -> authorize -> capability -> guardrails -> rate limit -> cache -> run (with
fallback) -> usage log -> envelope. Guardrail/limit blocks are logged as events.
"""

from __future__ import annotations

import uuid
from collections.abc import Awaitable, Callable

from ..cache import CacheManager
from ..config import Config
from ..core import envelope, errors
from ..guardrails import apply_output, check_input
from ..providers import Capability, Provider
from ..providers.health import CircuitBreaker
from ..ratelimit import RateLimiter, resolve_policies
from ..security import authenticate, authorize_feature
from ..usage import UsageLog, enforce_budget

# run(provider, model) -> (data, usage)
FeatureRun = Callable[[Provider, str | None], Awaitable[tuple[dict, dict]]]

# Errors that mean "this provider couldn't serve it — try the fallback".
# Excludes provider_safety_blocked: a safety refusal is a content decision, not an
# outage, so blindly retrying it on another provider is wrong.
FAILOVER_CODES = {
    "provider_error",
    "provider_timeout",
    "provider_rate_limited",
    "provider_invalid_response",
}

# Process-wide provider health. Module-level so it persists across requests.
circuit_breaker = CircuitBreaker()


async def _run_with_fallback(run, providers, feature_cfg, capability):
    """Run on the primary; on a failover-eligible error (or an open circuit), use the fallback.

    Returns (data, usage, provider, model).
    """
    primary = feature_cfg.provider
    provider = providers.get(primary)
    if provider is None:
        raise errors.internal_error(f"Provider {primary!r} is not available.")
    if capability not in provider.capabilities:
        raise errors.internal_error(f"Provider {primary!r} does not support {capability.value}.")
    fb = feature_cfg.fallback

    async def _fallback():
        """Run the fallback provider, or return None if there isn't a usable one."""
        if fb is None:
            return None
        fb_provider = providers.get(fb.provider)
        if fb_provider is None or capability not in fb_provider.capabilities:
            return None
        try:
            data, usage = await run(fb_provider, fb.model)
            circuit_breaker.record_success(fb.provider)
            return data, usage, fb.provider, fb.model
        except errors.SynthrError as exc:
            if exc.code in FAILOVER_CODES:
                circuit_breaker.record_failure(fb.provider)
            raise

    # Primary's circuit is open — skip it and go straight to the fallback if we have one.
    if circuit_breaker.is_open(primary):
        result = await _fallback()
        if result is not None:
            return result

    try:
        data, usage = await run(provider, feature_cfg.model)
        circuit_breaker.record_success(primary)
        return data, usage, primary, feature_cfg.model
    except errors.SynthrError as exc:
        if exc.code in FAILOVER_CODES:
            circuit_breaker.record_failure(primary)
        if exc.code not in FAILOVER_CODES:
            raise
        result = await _fallback()
        if result is None:
            raise
        return result


async def execute(
    feature: str,
    *,
    request_payload: dict,
    config: Config,
    providers: dict[str, Provider],
    cache: CacheManager,
    limiter: RateLimiter,
    usage: UsageLog,
    key: str | None,
    origin: str | None,
    user_id: str | None,
    capability: Capability,
    run: FeatureRun,
    guard_text: str | None = None,
) -> dict:
    request_id = "req_" + uuid.uuid4().hex[:12]

    try:
        auth = authenticate(config, key, origin)
    except errors.SynthrError as exc:
        usage.record_event(project="-", subject="-", kind=exc.code, detail=exc.message)
        raise

    feature_cfg = config.features.get(feature)
    if feature_cfg is None:
        raise errors.internal_error(f"Feature {feature!r} is not configured.")

    try:
        authorize_feature(auth, feature, feature_cfg)
    except errors.SynthrError as exc:
        usage.record_event(project=auth.project_id, subject=auth.key_id, kind=exc.code, detail=exc.message)
        raise

    subject = user_id or auth.key_id

    def block(exc: errors.SynthrError) -> None:
        usage.record_event(project=auth.project_id, subject=subject, kind=exc.code, detail=exc.message)

    try:
        check_input(guard_text, feature_cfg.guardrails)
        limiter.enforce(resolve_policies(config, auth.project_id, feature, subject))
        project_cfg = config.projects.get(auth.project_id)
        if project_cfg is not None:
            enforce_budget(usage, project_cfg.budget, auth.project_id, feature)
    except errors.SynthrError as exc:
        block(exc)
        raise

    def log(provider_name: str, model: str | None, cached: bool, usage_data: dict) -> None:
        usage.record(
            project=auth.project_id, subject=subject, feature=feature,
            provider=provider_name, model=model, cached=cached, usage=usage_data,
        )

    hit = cache.get(feature, feature_cfg.cache, request_payload, guard_text)
    if hit is not None:
        log(feature_cfg.provider, feature_cfg.model, cached=True, usage_data={})
        return envelope.success(hit, feature=feature, provider=feature_cfg.provider, cached=True, request_id=request_id)

    data, usage_data, served_by, served_model = await _run_with_fallback(run, providers, feature_cfg, capability)

    data, redacted = apply_output(data, feature_cfg.guardrails)
    if redacted:
        usage.record_event(project=auth.project_id, subject=subject, kind="output_redacted", detail="PII removed from response")

    cache.set(feature, feature_cfg.cache, request_payload, data, guard_text)  # caches the redacted output
    log(served_by, served_model, cached=False, usage_data=usage_data)

    return envelope.success(
        data, feature=feature, provider=served_by, cached=False, request_id=request_id, usage=usage_data
    )
