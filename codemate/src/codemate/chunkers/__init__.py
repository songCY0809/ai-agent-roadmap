"""分块策略。

三层策略（详见 docs/architecture.md §3.3）：
  1. 按结构切分（markdown 按标题、code 按函数）
  2. RecursiveCharacterTextSplitter 兜底压上限
  3. buildHeaderMeta：每个 chunk 前注入 <document_metadata>...</document_metadata>

W4 实现：fixed + recursive。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Chunk:
    """检索/索引单元。"""

    chunk_id: str
    doc_id: str
    chunk_source: str
    text: str               # 已包含 metadata header 的最终文本
    raw_text: str           # 不含 header 的原文（用于引用展示）
    metadata: dict[str, Any] = field(default_factory=dict)
