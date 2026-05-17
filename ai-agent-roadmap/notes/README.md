# 学习笔记入口 · 同时是 CodeMate 的知识库源

> **一句话**：在这里写 Markdown 笔记，W4 之后 CodeMate 直接 ingest 这个目录，**零迁移**。
> **写笔记的编辑器**：Cursor（你已经在用）+ Claude，把笔记当代码一样写。

## 目录速览

```text
notes/
├── README.md             ← 本文件
├── _templates/           ← 3 个模板（下划线开头，RAG 自动跳过）
│   ├── concept.md        ← 概念卡片模板
│   ├── crash.md          ← 翻车记录模板
│   └── weekly.md         ← 周总结模板
├── concepts/             ← 概念卡片（最常用，平均每天 1-2 张）
├── crashes/              ← 翻车记录（最值钱，遇 bug 立即写）
└── weekly/               ← 周总结（每个周日必写）
```

## 笔记类型选择指南

| 场景 | 用哪个模板 | 时机 |
|---|---|---|
| 学了一个新概念 / 新 API | `concept.md` | 当天结束前 5-15 min |
| 踩坑 / debug 1h 以上 | `crash.md` | 解决后立即写，趁热乎 |
| 周末复盘 / 简历素材沉淀 | `weekly.md` | 每周日下午 30 min |

## 命名约定

格式：`W<周>-<日期>-<slug>.md`

- 例 1：`concepts/W1-2026-05-12-pydantic-v2-basemodel.md`
- 例 2：`crashes/W3-2026-05-29-langgraph-deadloop.md`
- 例 3：`weekly/W1-2026-05-17-summary.md`

规则：

1. **周编号写最前**：`W1`-`W9`，对应 [`../weekly/`](../weekly/) 周计划
2. **日期 ISO 格式**：YYYY-MM-DD，方便 `ls` 自然排序
3. **slug 全小写连字符**：避免空格 / 中文 / 大写（CodeMate chunker 友好）
4. 周总结统一以 `-summary.md` 结尾

## YAML Frontmatter 规范

每篇笔记**必须**以下 6 个字段：

```yaml
---
title: Pydantic V2 BaseModel 用法     # 笔记标题（可含中文）
type: concept                        # concept | crash | weekly
week: W1                             # W1-W9
date: 2026-05-12                     # ISO 日期
tags: [python, pydantic, validation] # 关键词，3-5 个
status: draft                        # draft | reviewed | mastered
---
```

**可选**字段（推荐填）：

```yaml
source:                              # 学习参考链接
  - https://docs.pydantic.dev/latest/concepts/models/
related:                             # 相关笔记的相对路径
  - ../concepts/W1-2026-05-13-openai-function-calling.md
```

这些字段在 W4 之后会被 CodeMate `loaders/markdown.py` 解析成 chunk metadata，支持：

- 按周筛选：`week=W3`
- 按类型筛选：`type=crash` 看翻车库
- 按标签筛选：`tags contains pydantic` 找出所有 Pydantic 相关
- 按掌握度筛选：`status=draft` 看未复习的概念

## Cursor 工作流（今天就能用）

### 方式 1：纯手工（30 秒/篇）

1. 在 Cursor 里 `Cmd+N` 新建文件
2. 路径选 `notes/concepts/W1-2026-05-12-pydantic-v2-basemodel.md`
3. 打开 `_templates/concept.md` 全选复制 → 粘贴 → 改 title/date/tags
4. 写内容
5. `git add . && git commit -m "notes(W1): pydantic v2 basics"`

### 方式 2：一键 CLI（推荐，5 秒/篇）

```bash
python tools/new-note.py concept "Pydantic V2 BaseModel"
# 自动生成 notes/concepts/W1-2026-05-12-pydantic-v2-basemodel.md
# 自动填好 frontmatter
# 自动打开 Cursor
```

详见 [`../../tools/new-note.py`](../../tools/new-note.py)。

### 方式 3：让 Claude 帮你写

在 Cursor 里选中你刚学的代码片段，按 `Cmd+L`，问：

- 「基于这段代码，按 `notes/_templates/concept.md` 的格式写一份概念卡片」
- 「读 `notes/concepts/` 里所有 Pydantic 相关笔记，找出 3 个错误说法」
- 「基于这段 debug 经历，按 `crash.md` 模板写一份翻车记录」

## 与 CodeMate 知识库（W4+）的对接

### 写笔记时你不用做任何事

只要按规范写 `.md`，CodeMate W4 启动后会自动 ingest。

### W4 ingestion 命令（提前埋点）

```bash
cd codemate
codemate ingest \
  --source ../ai-agent-roadmap/notes/concepts \
  --source ../ai-agent-roadmap/notes/crashes \
  --source ../ai-agent-roadmap/notes/weekly
```

`_templates/` 因下划线开头被 `loaders/markdown.py` 跳过，不会污染向量库。

### Frontmatter → Metadata 映射（W4 实现要点）

```python
# codemate/src/codemate/loaders/markdown.py
import frontmatter

def load(filepath):
    post = frontmatter.load(filepath)
    return DocumentRecord(
        content=post.content,
        metadata={
            "source": str(filepath),
            "week": post.get("week"),
            "type": post.get("type"),
            "tags": post.get("tags", []),
            "status": post.get("status"),
            "title": post.get("title"),
        },
    )
```

### 未来的 RAG 查询示例

| 你问 CodeMate | 它怎么查 |
|---|---|
| "我 W3 学了哪些 LangGraph 概念？" | filter `week=W3 AND tags contains langgraph` |
| "我有哪些 RAG 翻车记录？" | filter `type=crash AND tags contains rag` |
| "未掌握的概念有哪些？" | filter `status=draft AND type=concept` |
| "上周末总结怎么说的？" | filter `type=weekly ORDER BY date DESC LIMIT 1` |

## 写笔记的反模式（避雷）

- **不要 Obsidian wikilink** `[[xxx]]`：用相对路径 `[xxx](../concepts/W1-xxx.md)`，否则 CodeMate 解析不出来
- **不要纯 emoji 标题**：chunker 切分依赖 `## 标题`，纯 emoji 会丢失语义
- **不要把代码全部塞在一个 fenced block 里**：每个代码块 < 30 行，超过就拆
- **不要写"我懂了"就完事**：必填「自测 3 题」+「容易踩的坑」，否则两周后看不懂
- **不要漏 frontmatter**：W4 ingestion 看不到 metadata 就只能按文件名做粗筛

## 示例笔记（W1 开始填）

W1 期间应该产出的笔记（参考量，不强制）：

- `concepts/W1-2026-05-12-openai-function-calling.md`（Day 2 学完写）
- `concepts/W1-2026-05-13-pydantic-v2-basemodel.md`（Day 2 学完写）
- `concepts/W1-2026-05-14-react-loop-mechanism.md`（Day 3 学完写）
- `concepts/W1-2026-05-15-async-await-in-python.md`（Day 5 学完写）
- `crashes/W1-2026-05-XX-XXX.md`（遇到 bug 时立即写）
- `weekly/W1-2026-05-17-summary.md`（Sun 必写）

## 状态字段的生命周期

```text
draft     ← 写完初稿（默认）
   ↓ 一周后回头看，能讲清楚 = reviewed
reviewed
   ↓ 一个月后还能讲清楚 / 面试被问到能脱口而出 = mastered
mastered
```

每周日写 `weekly.md` 时顺手把对应 `concepts/` 的 status 升级一档。

## FAQ

**Q：能用 Obsidian 同时打开吗？**
A：能。Obsidian Open Folder 选 `notes/` 即可，但**不要用 wikilink 语法**，保持纯 Markdown。

**Q：可以中文文件名吗？**
A：不可以。slug 必须 ASCII 小写连字符，否则 chunker / 向量库都可能出问题。中文写在 frontmatter.title 和正文里。

**Q：写错地方了怎么办？**
A：`git mv` 移动文件，frontmatter.type 同步改，weekly.md 里更新链接。

**Q：图片放哪？**
A：W4 之前先不管，本地截图直接拖进 Cursor，存到 `notes/_assets/` 下，命名 `WX-YYYY-MM-DD-xxx.png`。W4 ingestion 暂不处理图片，但路径会保留。

**Q：要不要在 GitHub 上 public？**
A：W9 准备简历时 public，平时 private 即可。翻车记录尤其敏感不要太早公开。
