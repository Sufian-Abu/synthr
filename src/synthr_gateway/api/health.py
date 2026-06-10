"""Root index + liveness/info."""

from __future__ import annotations

from fastapi import APIRouter, Depends

from ..config import Config
from .deps import get_config

router = APIRouter(tags=["system"])


@router.get("/", include_in_schema=False)
async def index() -> dict:
    return {
        "name": "Synthr Gateway",
        "api_reference": "/redoc",
        "dashboard": "/dashboard",
        "health": "/health",
    }


@router.get("/health")
async def health(config: Config = Depends(get_config)) -> dict:
    return {
        "status": "ok",
        "features": list(config.features),
        "providers": list(config.providers),
    }
