"""classify — single-label classification over caller-defined labels."""

from .models import ClassifyRequest
from .service import classify

__all__ = ["ClassifyRequest", "classify"]
