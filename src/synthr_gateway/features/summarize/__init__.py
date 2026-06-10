"""summarize — concise summary of a block of text."""

from .models import SummarizeRequest
from .service import summarize

__all__ = ["SummarizeRequest", "summarize"]
