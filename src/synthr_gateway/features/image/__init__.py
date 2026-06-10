"""image — text-to-image generation (SPEC.md §6.2)."""

from .models import ImageRequest
from .service import generate_image

__all__ = ["ImageRequest", "generate_image"]
