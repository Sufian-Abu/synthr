"""Provider adapters (adapter pattern) + the registry that builds them from config."""

from .base import Provider
from .registry import build_providers
from .types import Capability, CompletionResult, ImageResult, Message, ToolCall

__all__ = [
    "Provider",
    "build_providers",
    "Capability",
    "CompletionResult",
    "ImageResult",
    "Message",
    "ToolCall",
]
