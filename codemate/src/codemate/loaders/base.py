"""Loader 基类 + DocumentRecord 标准 schema。

设计来源：AnythingLLM `collector/processSingleFile/index.js` 的 LOADER_REGISTRY 模式
+ 标准化文档 schema（参见 docs/phase0-investigation.md §3.3）。

所有 loader 输出统一的 DocumentRecord，下游 chunker / embedder 无需关心来源。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterator, Protocol


@dataclass
class DocumentRecord:
    """A loaded document, language-agnostic and source-agnostic.

    Attributes:
        doc_id: 稳定 ID（用于增量更新 / 删除对齐）。建议 hash(chunk_source) 或源 ID。
        title: 标题（用于引用展示）。
        chunk_source: 类 URI 字符串，如 ``file:///path``、``yuque://book/123``。
            借鉴 AnythingLLM 的 chunkSource 概念。
        page_content: 主体文本（chunking 前的整段）。
        metadata: 自由 metadata，建议保留 page / section / line / published / lang 等。
    """

    doc_id: str
    title: str
    chunk_source: str
    page_content: str
    metadata: dict[str, Any] = field(default_factory=dict)


class Loader(Protocol):
    """Loader 协议。

    实现类只需要：``def load(self, path: Path) -> Iterator[DocumentRecord]``。
    一个文件可以产出多个 DocumentRecord（例如 mbox 一封邮件一条、xlsx 一个 sheet 一条）。
    """

    def load(self, path: Path) -> Iterator[DocumentRecord]:  # pragma: no cover - protocol
        ...
