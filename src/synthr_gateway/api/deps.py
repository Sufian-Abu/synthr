"""FastAPI dependencies — pull shared singletons off app state."""

from __future__ import annotations

from fastapi import Request

from ..cache import CacheManager
from ..config import Config
from ..jobs import JobManager, JobStore
from ..providers import Provider
from ..ratelimit import RateLimiter
from ..usage import UsageLog


def get_config(request: Request) -> Config:
    return request.app.state.config


def get_providers(request: Request) -> dict[str, Provider]:
    return request.app.state.providers


def get_cache(request: Request) -> CacheManager:
    return request.app.state.cache


def get_usage(request: Request) -> UsageLog:
    return request.app.state.usage


def get_limiter(request: Request) -> RateLimiter:
    return request.app.state.limiter


def get_jobs_store(request: Request) -> JobStore:
    return request.app.state.jobs_store


def get_jobs(request: Request) -> JobManager:
    return request.app.state.jobs
