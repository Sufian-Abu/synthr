"""chat orchestration — run a raw completion and shape it for the OpenAI envelope."""

from __future__ import annotations

from ...providers import Message, Provider
from .models import ChatMessage


async def chat_complete(
    provider: Provider,
    model: str,
    messages: list[ChatMessage],
    tools: list[dict] | None,
    temperature: float,
) -> tuple[dict, dict]:
    msgs = [Message(m.role, m.content or "") for m in messages]
    result = await provider.complete(msgs, model=model, temperature=temperature, tools=tools)
    data = {
        "content": result.text,
        "tool_calls": [{"id": tc.id, "name": tc.name, "arguments": tc.arguments} for tc in result.tool_calls],
        "finish_reason": result.finish_reason or ("tool_calls" if result.tool_calls else "stop"),
    }
    return data, result.usage
