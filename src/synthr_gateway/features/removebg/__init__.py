"""removeBackground — strip an image's background (SPEC.md §6.3)."""

from .models import RemoveBackgroundRequest
from .service import remove_background

__all__ = ["RemoveBackgroundRequest", "remove_background"]
