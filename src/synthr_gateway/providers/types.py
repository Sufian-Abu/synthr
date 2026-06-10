"""Shared provider data types."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum


class Capability(str, Enum):
    TEXT = "text"
    IMAGE = "image"
    REMOVE_BACKGROUND = "remove_background"


@dataclass
class Message:
    role: str  # "system" | "user" | "assistant"
    content: str


@dataclass
class CompletionResult:
    text: str
    model: str
    usage: dict = field(default_factory=dict)  # {prompt_tokens, completion_tokens}
    raw: dict | None = None


@dataclass
class ImageResult:
    images: list[dict]  # each: {"b64": ..., "mime": ...} or {"url": ...}
    model: str
    raw: dict | None = None
