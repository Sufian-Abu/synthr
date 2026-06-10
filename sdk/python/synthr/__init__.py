"""Synthr Python SDK — call gateway features without touching HTTP.

    from synthr import AI
    ai = AI(key="sk_proj_...")            # url defaults to http://localhost:8000
    ai.fill_form(fields=[...], context="...")
    ai.summarize(text="...", max_words=20)
"""

from .client import AI, AsyncAI
from .errors import SynthrError

__all__ = ["AI", "AsyncAI", "SynthrError"]
__version__ = "0.1.0"
