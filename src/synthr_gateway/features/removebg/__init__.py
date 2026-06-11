"""removeBackground — strip an image's background."""

from .models import RemoveBackgroundRequest
from .service import remove_background

__all__ = ["RemoveBackgroundRequest", "remove_background"]
