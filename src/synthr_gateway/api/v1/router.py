"""Aggregates all v1 feature routes under the /v1 prefix."""

from __future__ import annotations

from fastapi import APIRouter

from .chat import router as chat_router
from .fillform import router as fillform_router
from .image import router as image_router
from .removebg import router as removebg_router
from .summarize import router as summarize_router
from .translate import router as translate_router

router = APIRouter(prefix="/v1", tags=["features"])
for r in (fillform_router, image_router, removebg_router, summarize_router, translate_router, chat_router):
    router.include_router(r)
