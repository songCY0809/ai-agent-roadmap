"""LLM 客户端抽象。

接口形态借鉴 Khoj `processor/embeddings.py:EmbeddingsModel` 的本地/远端分叉模式。

W1 实现 DeepSeekClient（OpenAI-compatible API）。
W2 实现 LocalLlamaClient（llama.cpp server，也是 OpenAI-compatible）。
W6 加 fallback 路由（主线 429 / 超时 → 切备线）。
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, AsyncIterator, Literal, Protocol


@dataclass
class Message:
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    tool_call_id: str | None = None
    name: str | None = None


@dataclass
class ToolSchema:
    name: str
    description: str
    parameters: dict[str, Any]   # JSON Schema


@dataclass
class ToolCallResult:
    content: str
    tool_calls: list[dict[str, Any]] | None = None
    finish_reason: str = "stop"


class LLMClient(Protocol):
    async def chat(
        self,
        messages: list[Message],
        temperature: float = 0.3,
        **kwargs: Any,
    ) -> AsyncIterator[str]:  # pragma: no cover - protocol
        """流式返回文本片段。"""
        ...

    async def chat_with_tools(
        self,
        messages: list[Message],
        tools: list[ToolSchema],
        **kwargs: Any,
    ) -> ToolCallResult:  # pragma: no cover - protocol
        """带工具调用的非流式接口（首版）。"""
        ...
