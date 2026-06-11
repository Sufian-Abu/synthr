"""Feature dispatch table — maps a feature name to its request model, capability, service,
and a guard-text extractor. Used by the jobs API to run any feature generically."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel

from ..providers import Capability, Provider
from .classify import ClassifyRequest, classify
from .embed import EmbedRequest, embed
from .extract import ExtractRequest, extract
from .fillform import FillFormRequest, fill_form
from .generate import GenerateRequest, generate
from .image import ImageRequest, generate_image
from .moderate import ModerateRequest, moderate
from .ocr import OcrRequest, ocr
from .removebg import RemoveBackgroundRequest, remove_background
from .rewrite import RewriteRequest, rewrite
from .seo import SeoRequest, seo
from .summarize import SummarizeRequest, summarize
from .translate import TranslateRequest, translate


@dataclass
class FeatureSpec:
    model: type[BaseModel]
    capability: Capability
    service: Callable[[Any, Provider, str | None], Awaitable[tuple[dict, dict]]]
    guard: Callable[[Any], str | None]


def _attr(name: str) -> Callable[[Any], str | None]:
    return lambda body: getattr(body, name, None)


DISPATCH: dict[str, FeatureSpec] = {
    "fillForm": FeatureSpec(FillFormRequest, Capability.TEXT, fill_form, lambda b: str(b.context)),
    "summarize": FeatureSpec(SummarizeRequest, Capability.TEXT, summarize, _attr("text")),
    "translate": FeatureSpec(TranslateRequest, Capability.TEXT, translate, _attr("text")),
    "rewrite": FeatureSpec(RewriteRequest, Capability.TEXT, rewrite, _attr("text")),
    "generate": FeatureSpec(GenerateRequest, Capability.TEXT, generate, _attr("prompt")),
    "seo": FeatureSpec(SeoRequest, Capability.TEXT, seo, _attr("content")),
    "classify": FeatureSpec(ClassifyRequest, Capability.TEXT, classify, _attr("text")),
    "extract": FeatureSpec(ExtractRequest, Capability.TEXT, extract, _attr("text")),
    "moderate": FeatureSpec(ModerateRequest, Capability.TEXT, moderate, _attr("text")),
    "embed": FeatureSpec(
        EmbedRequest, Capability.EMBED, embed, lambda b: b.input if isinstance(b.input, str) else " ".join(b.input)
    ),
    "image": FeatureSpec(ImageRequest, Capability.IMAGE, generate_image, _attr("prompt")),
    "removeBackground": FeatureSpec(
        RemoveBackgroundRequest, Capability.REMOVE_BACKGROUND, remove_background, lambda b: None
    ),
    "ocr": FeatureSpec(OcrRequest, Capability.VISION, ocr, lambda b: None),
}
