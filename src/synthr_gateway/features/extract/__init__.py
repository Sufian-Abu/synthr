"""extract — pull a list of structured records from free text."""

from .models import ExtractRequest
from .service import extract

__all__ = ["ExtractRequest", "extract"]
