"""chat — OpenAI-compatible chat completions over the Synthr pipeline."""

from .models import ChatCompletionRequest, ChatMessage
from .service import chat_complete

__all__ = ["ChatCompletionRequest", "ChatMessage", "chat_complete"]
