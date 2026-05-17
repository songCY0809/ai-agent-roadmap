# tools/

学习路径 / CodeMate 项目的辅助脚本。

## new-note.py · 一键建学习笔记

```bash
# 概念卡片
python tools/new-note.py concept "Pydantic V2 BaseModel"
python tools/new-note.py concept "OpenAI Function Calling" --tags python,llm

# 翻车记录
python tools/new-note.py crash "ReAct loop 死循环"

# 周总结 (周日跑一次)
python tools/new-note.py weekly

# 跨周写 (回头补) - 显式指定
python tools/new-note.py concept "..." --week W3 --date 2026-05-30

# 不自动打开 Cursor
python tools/new-note.py concept "..." --no-open
```

行为:

- 自动算当前是第几周 (W1 = 2026-05-11)
- 自动写入 `ai-agent-roadmap/notes/<concepts|crashes|weekly>/`
- 自动填好 frontmatter (title / type / week / date / tags / status)
- 自动从 `_templates/` 加载模板正文
- 自动 `cursor <file>` 打开 (回退到 `code`)

依赖: 纯 Python 3.10+ stdlib，零三方包。

详细规范见 [`../ai-agent-roadmap/notes/README.md`](../ai-agent-roadmap/notes/README.md)。
