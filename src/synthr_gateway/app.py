"""Application factory: wires config, storage, providers, cache, usage, limiter, routes.

Run for dev:  uvicorn "synthr_gateway.app:create_app" --factory --reload
"""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api.health import router as health_router
from .api.v1.router import router as v1_router
from .cache import CacheManager
from .config import load_config
from .config.preflight import run_preflight
from .core.envelope import error_payload
from .core.errors import SynthrError
from .dashboard import router as dashboard_router
from .jobs import JobManager, JobStore
from .providers.registry import build_providers
from .ratelimit import RateLimiter
from .storage import Database
from .usage import UsageLog

DESCRIPTION = """
Self-hosted, batteries-included **AI-capabilities** gateway.

- **Auth:** send your project key in the `X-Project-Key` header (secret `sk_proj_…` for
  backend/REST; public `pk_proj_…` for browsers, from an allowed origin).
- **Dashboard:** [`/dashboard`](/dashboard) · **Health:** [`/health`](/health)

This is a read-only API reference. Call endpoints from the SDKs, `curl`, or your app —
see the project README.
"""


def create_app(config_path: str | Path | None = None) -> FastAPI:
    app = FastAPI(
        title="Synthr Gateway",
        version="0.1.0",
        description=DESCRIPTION,
        docs_url=None,  # Swagger UI disabled; ReDoc (/redoc) is the API reference
        openapi_tags=[
            {"name": "features", "description": "AI capabilities — call a feature, never a prompt or provider."},
            {"name": "system", "description": "Health and service info."},
        ],
    )

    config = load_config(config_path)
    run_preflight(config)  # warn on dev-secret / plaintext keys / open public keys
    db = Database(config.gateway.db_path)

    app.state.config = config
    app.state.db = db
    app.state.providers = build_providers(config)
    app.state.cache = CacheManager(db)
    app.state.usage = UsageLog(db)
    app.state.limiter = RateLimiter(db)
    jobs_store = JobStore(db)
    app.state.jobs_store = jobs_store
    app.state.jobs = JobManager(jobs_store)

    # CORS so browsers can use public keys cross-origin. The allow-list is exactly the
    # origins declared on public (pk_proj_) keys — no wildcard.
    cors_origins = sorted(
        {o for p in config.projects.values() for k in p.keys if k.type == "public" for o in k.allowed_origins}
    )
    if cors_origins:
        app.add_middleware(
            CORSMiddleware,
            allow_origins=cors_origins,
            allow_methods=["GET", "POST", "OPTIONS"],
            allow_headers=["Content-Type", "X-Project-Key", "X-User-Id", "Authorization"],
        )

    @app.exception_handler(SynthrError)
    async def _handle_nexus_error(_: Request, exc: SynthrError) -> JSONResponse:
        return JSONResponse(status_code=exc.http_status, content=error_payload(exc))

    app.include_router(health_router)
    app.include_router(v1_router)
    app.include_router(dashboard_router)
    return app
