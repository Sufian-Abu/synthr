"""embed — text to vector(s)."""

from .models import EmbedRequest
from .service import embed

__all__ = ["EmbedRequest", "embed"]
