"""Request model for the OpenAI-compatible chat endpoint."""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel


class ChatMessage(BaseModel):
    role: str  # "system" | "user" | "assistant" | "tool"
    content: str | None = None


class ChatCompletionRequest(BaseModel):
    model: str
    messages: list[ChatMessage]
    temperature: float = 0.0
    stream: bool = False
    tools: list[dict] | None = None
    tool_choice: Any | None = None  # accepted, passed through where supported
    max_tokens: int | None = None  # accepted for compatibility

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "model": "gemini-flash-latest",
                    "messages": [{"role": "user", "content": "Say hello in one word."}],
                }
            ]
        }
    }
