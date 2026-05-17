#!/usr/bin/env python3
"""
一键建笔记 CLI。

用法:
    python tools/new-note.py concept "Pydantic V2 BaseModel"
    python tools/new-note.py crash "ReAct loop 死循环"
    python tools/new-note.py weekly                          # 自动用本周编号
    python tools/new-note.py concept "..." --week W2         # 显式指定周
    python tools/new-note.py concept "..." --tags python,pydantic
    python tools/new-note.py concept "..." --no-open         # 不自动打开 Cursor

依赖: 仅 Python 3.10+ stdlib (argparse / datetime / pathlib / re / shutil / subprocess)。

设计要点:
- 自动识别当前周 (基于路线图 W1=2026-05-11 起始日)
- slug 用纯 ASCII 小写连字符 (chunker 友好)
- 同名文件冲突时自动追加 -2/-3
- 自动打开 Cursor (有 PATH 里的 `cursor` 命令时)
- 路径 hardcoded 到 ai-agent-roadmap/notes/，不依赖配置文件
"""

from __future__ import annotations

import argparse
import datetime as dt
import re
import shutil
import subprocess
import sys
from pathlib import Path

# 路线图 W1 起始日 (周一)
W1_START = dt.date(2026, 5, 11)

REPO_ROOT = Path(__file__).resolve().parent.parent
NOTES_ROOT = REPO_ROOT / "ai-agent-roadmap" / "notes"

SUBDIR_BY_TYPE = {
    "concept": "concepts",
    "crash": "crashes",
    "weekly": "weekly",
}


def compute_week(today: dt.date) -> str:
    """根据路线图起始日推算当前是第几周。早于 W1 返回 W1，超过 W9 返回 W9+"""
    delta_days = (today - W1_START).days
    if delta_days < 0:
        return "W1"
    week_num = delta_days // 7 + 1
    if week_num > 9:
        return f"W{week_num}"
    return f"W{week_num}"


def slugify(text: str) -> str:
    """中英混合标题转 ASCII 小写连字符。简化版，不依赖第三方库。"""
    text = text.strip().lower()
    text = re.sub(r"[\s_]+", "-", text)
    text = re.sub(r"[^a-z0-9\-]+", "", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text or "untitled"


def render_frontmatter(
    title: str,
    note_type: str,
    week: str,
    date: dt.date,
    tags: list[str],
    status: str,
) -> str:
    tags_yaml = "[" + ", ".join(tags) + "]" if tags else "[]"
    return (
        "---\n"
        f"title: {title}\n"
        f"type: {note_type}\n"
        f"week: {week}\n"
        f"date: {date.isoformat()}\n"
        f"tags: {tags_yaml}\n"
        "source: []\n"
        "related: []\n"
        f"status: {status}\n"
        "---\n\n"
    )


_TEMPLATE_HINT_PATTERN = re.compile(
    r"^>\s*模板说明[\s\S]*?(?=\n\n)\n*",
    re.MULTILINE,
)


def load_template_body(note_type: str) -> str:
    """从 _templates/ 加载模板正文 (跳过 frontmatter + 跳过给"手工复制"用的模板说明块)。"""
    tpl_path = NOTES_ROOT / "_templates" / f"{note_type}.md"
    if not tpl_path.exists():
        return f"# {note_type}\n\n(模板缺失: {tpl_path})\n"
    text = tpl_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    if len(parts) >= 3:
        body = parts[2].lstrip("\n")
    else:
        body = text
    body = _TEMPLATE_HINT_PATTERN.sub("", body, count=1).lstrip("\n")
    return body


def resolve_target_path(
    note_type: str, week: str, date: dt.date, slug: str
) -> Path:
    subdir = NOTES_ROOT / SUBDIR_BY_TYPE[note_type]
    subdir.mkdir(parents=True, exist_ok=True)
    if note_type == "weekly":
        base = f"{week}-{date.isoformat()}-summary"
    else:
        base = f"{week}-{date.isoformat()}-{slug}"
    target = subdir / f"{base}.md"
    counter = 2
    while target.exists():
        target = subdir / f"{base}-{counter}.md"
        counter += 1
    return target


def open_in_cursor(path: Path) -> None:
    """优先尝试 `cursor`，回退 `code`，再回退打印路径。"""
    for cmd in ("cursor", "code"):
        if shutil.which(cmd):
            try:
                subprocess.Popen([cmd, str(path)])
                print(f"已用 {cmd} 打开: {path}")
                return
            except OSError:
                continue
    print(f"未找到 cursor / code 命令，请手动打开: {path}")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="一键建笔记，写入 ai-agent-roadmap/notes/ 并打开 Cursor",
    )
    parser.add_argument(
        "type",
        choices=["concept", "crash", "weekly"],
        help="笔记类型",
    )
    parser.add_argument(
        "title",
        nargs="?",
        default=None,
        help="笔记标题 (weekly 类型可省略)",
    )
    parser.add_argument("--week", default=None, help="覆盖周编号，如 W3")
    parser.add_argument(
        "--date",
        default=None,
        help="覆盖日期 ISO 格式 (YYYY-MM-DD)，默认今天",
    )
    parser.add_argument(
        "--tags",
        default="",
        help="逗号分隔的标签，如 python,pydantic",
    )
    parser.add_argument(
        "--status",
        default=None,
        help="覆盖 status (默认 concept=draft, crash=resolved, weekly=draft)",
    )
    parser.add_argument(
        "--no-open",
        action="store_true",
        help="不自动打开 Cursor",
    )
    args = parser.parse_args()

    today = (
        dt.date.fromisoformat(args.date) if args.date else dt.date.today()
    )
    week = args.week or compute_week(today)

    if args.type == "weekly":
        title = args.title or f"{week} 周总结"
        slug = ""
    else:
        if not args.title:
            parser.error(f"{args.type} 类型必须提供 title")
        title = args.title
        slug = slugify(title)

    default_status = {"concept": "draft", "crash": "resolved", "weekly": "draft"}
    status = args.status or default_status[args.type]
    tags = [t.strip() for t in args.tags.split(",") if t.strip()]

    target = resolve_target_path(args.type, week, today, slug)

    body = load_template_body(args.type)
    frontmatter = render_frontmatter(title, args.type, week, today, tags, status)
    target.write_text(frontmatter + body, encoding="utf-8")

    print(f"已创建笔记: {target.relative_to(REPO_ROOT)}")
    print(f"  type={args.type}  week={week}  date={today.isoformat()}")
    if tags:
        print(f"  tags={tags}")

    if not args.no_open:
        open_in_cursor(target)

    return 0


if __name__ == "__main__":
    sys.exit(main())
