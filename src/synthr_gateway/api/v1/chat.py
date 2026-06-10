"""POST /v1/chat/completions — drop-in OpenAI-compatible endpoint.

Point the official OpenAI SDK (or LangChain, the Vercel AI SDK, etc.) at this gateway and
keep your code: same request/response shape, but every call runs through Synthr's pipeline
(auth, guardrails, rate limits, cache, provider fallback, cost logging). Auth accepts
`Authorization: Bearer <project-key>` (what the OpenAI SDK sends) or `X-Project-Key`.

The provider is chosen by the `chat` feature in config; the request's `model` is forwarded
to it. `stream: true` returns OpenAI-style SSE chunks; `tools` are passed through and tool
calls come back on the message.
"""

from __future__ import annotations

import json
import time
import uuid
from collections.abc import AsyncIterator

from fastapi import APIRouter, Depends, Header
from fastapi.responses import JSONResponse, StreamingResponse

from ...cache import CacheManager
from ...config import Config
from ...core import errors
from ...features.chat import ChatCompletionRequest, chat_complete
from ...guardrails import check_input
from ...providers import Capability, Message, Provider
from ...ratelimit import RateLimiter, resolve_policies
from ...security import authenticate, authorize_feature
from ...usage import UsageLog
from ..deps import get_cache, get_config, get_limiter, get_providers, get_usage
from ..runner import execute

router = APIRouter()

FEATURE = "chat"


def _key(authorization: str | None, x_project_key: str | None) -> str | None:
    if authorization and authorization.lower().startswith("bearer "):
        return authorization[7:].strip()
    return x_project_key


def _user_text(body: ChatCompletionRequest) -> str:
    return "\n".join(m.content or "" for m in body.messages if m.role != "system")


def _error_response(exc: errors.SynthrError) -> JSONResponse:
    """OpenAI-style error envelope, so SDK clients parse failures correctly."""
    return JSONResponse(
        status_code=exc.http_status,
        content={"error": {"message": exc.message, "type": exc.code, "code": exc.code}},
    )


def _to_response(envelope: dict, model: str) -> dict:
    data, meta = envelope["data"], envelope["meta"]
    message: dict = {"role": "assistant", "content": data.get("content")}
    if data.get("tool_calls"):
        message["tool_calls"] = [
            {
                "id": tc["id"] or f"call_{i}",
                "type": "function",
                "function": {"name": tc["name"], "arguments": tc["arguments"]},
            }
            for i, tc in enumerate(data["tool_calls"])
        ]
    usage = meta.get("usage") or {}
    pt, ct = usage.get("prompt_tokens", 0), usage.get("completion_tokens", 0)
    return {
        "id": "chatcmpl-" + meta["request_id"].split("_")[-1],
        "object": "chat.completion",
        "created": int(time.time()),
        "model": model,
        "choices": [{"index": 0, "message": message, "finish_reason": data.get("finish_reason") or "stop"}],
        "usage": {"prompt_tokens": pt, "completion_tokens": ct, "total_tokens": pt + ct},
        "x_synthr": {"provider": meta.get("provider"), "cached": meta.get("cached", False)},
    }


@router.post(
    "/chat/completions",
    summary="OpenAI-compatible chat completions",
    description=(
        "Drop-in for the OpenAI Chat Completions API. Point any OpenAI SDK at this gateway "
        "(`base_url=.../v1`) using your Synthr project key. Supports `stream` and `tools`. "
        "Auth: `Authorization: Bearer <project-key>` or `X-Project-Key`."
    ),
    tags=["features"],
)
async def chat_completions(
    body: ChatCompletionRequest,
    config: Config = Depends(get_config),
    providers: dict[str, Provider] = Depends(get_providers),
    cache: CacheManager = Depends(get_cache),
    limiter: RateLimiter = Depends(get_limiter),
    usage: UsageLog = Depends(get_usage),
    authorization: str | None = Header(default=None),
    x_project_key: str | None = Header(default=None),
    x_user_id: str | None = Header(default=None),
    origin: str | None = Header(default=None),
):
    key = _key(authorization, x_project_key)

    if body.stream:
        return await _streaming(body, config, providers, limiter, usage, key, origin, x_user_id)

    try:
        envelope = await execute(
            FEATURE,
            request_payload=body.model_dump(),
            config=config,
            providers=providers,
            cache=cache,
            limiter=limiter,
            usage=usage,
            key=key,
            origin=origin,
            user_id=x_user_id,
            capability=Capability.TEXT,
            run=lambda provider, _model: chat_complete(provider, body.model, body.messages, body.tools, body.temperature),
            guard_text=_user_text(body),
        )
    except errors.SynthrError as exc:
        return _error_response(exc)
    return _to_response(envelope, body.model)


def _chunk(cid: str, created: int, model: str, delta: dict, finish: str | None) -> dict:
    return {
        "id": cid,
        "object": "chat.completion.chunk",
        "created": created,
        "model": model,
        "choices": [{"index": 0, "delta": delta, "finish_reason": finish}],
    }


def _sse(obj: dict) -> str:
    return f"data: {json.dumps(obj)}\n\n"


async def _streaming(body, config, providers, limiter, usage, key, origin, user_id):
    try:
        auth = authenticate(config, key, origin)
        feature_cfg = config.features.get(FEATURE)
        if feature_cfg is None:
            raise errors.internal_error("Feature 'chat' is not configured.")
        authorize_feature(auth, FEATURE, feature_cfg)
        subject = user_id or auth.key_id
        check_input(_user_text(body), feature_cfg.guardrails)
        limiter.enforce(resolve_policies(config, auth.project_id, FEATURE, subject))
        provider = providers.get(feature_cfg.provider)
        if provider is None or Capability.TEXT not in provider.capabilities:
            raise errors.internal_error(f"Provider {feature_cfg.provider!r} can't serve chat.")
        gen = _event_stream(body, provider, feature_cfg.provider, usage, auth.project_id, subject)
        return StreamingResponse(gen, media_type="text/event-stream")
    except errors.SynthrError as exc:
        return _error_response(exc)


async def _event_stream(body, provider, provider_name, usage, project, subject) -> AsyncIterator[str]:
    cid = "chatcmpl-" + uuid.uuid4().hex[:24]
    created = int(time.time())
    msgs = [Message(m.role, m.content or "") for m in body.messages]

    yield _sse(_chunk(cid, created, body.model, {"role": "assistant"}, None))
    try:
        if provider.supports_streaming:
            async for delta in provider.stream_complete(msgs, model=body.model, temperature=body.temperature):
                yield _sse(_chunk(cid, created, body.model, {"content": delta}, None))
        else:  # graceful: providers without streaming get one full chunk
            result = await provider.complete(msgs, model=body.model, temperature=body.temperature)
            if result.text:
                yield _sse(_chunk(cid, created, body.model, {"content": result.text}, None))
    except errors.SynthrError as exc:
        yield _sse({"error": {"message": exc.message, "type": exc.code, "code": exc.code}})
        yield "data: [DONE]\n\n"
        usage.record_event(project=project, subject=subject, kind=exc.code, detail=exc.message)
        return

    yield _sse(_chunk(cid, created, body.model, {}, "stop"))
    yield "data: [DONE]\n\n"
    usage.record(project=project, subject=subject, feature=FEATURE, provider=provider_name, model=body.model, cached=False, usage={})
