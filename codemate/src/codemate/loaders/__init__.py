"""文档加载器。

LOADER_REGISTRY 模式借鉴 AnythingLLM `collector/utils/constants.js`：
ext → Loader 类的映射，未知扩展回退当 .txt 处理。

W4 实现：markdown / docx / txt
W4 末 / W5 加：语雀 API
W5+ 选做：PDF（注意保留 page 在 metadata，避免 AnythingLLM 的 flatten 陷阱）
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterator

from .base import DocumentRecord, Loader

# W4 真正实现这些 Loader 后取消注释
# from .markdown import MarkdownLoader
# from .docx import DocxLoader
# from .text import TextLoader
# from .yuque import YuqueLoader

LOADER_REGISTRY: dict[str, type[Loader]] = {
    # ".md": MarkdownLoader,
    # ".markdown": MarkdownLoader,
    # ".docx": DocxLoader,
    # ".txt": TextLoader,
}


def load_path(path: Path) -> Iterator[DocumentRecord]:
    """按扩展名分派到对应 Loader。未知扩展回退当文本处理（学 AnythingLLM）。"""
    raise NotImplementedError("W4 实现：填充 LOADER_REGISTRY 后实现")


__all__ = ["DocumentRecord", "Loader", "LOADER_REGISTRY", "load_path"]
