"""generate — freeform prompt to text."""

from .models import GenerateRequest
from .service import generate

__all__ = ["GenerateRequest", "generate"]
