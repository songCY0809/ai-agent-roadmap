"""CodeMate CLI 入口。

Usage:
    codemate hello                     # 简单测试 LLM 连通性（W1 必做）
    codemate ingest <path>             # 导入笔记目录（W4 起）
    codemate ask "<question>"          # 提问（W4 起）
    codemate practice --weak <tag>     # 算法陪练（W5 起）

构建命令：W1 hello、W4 ingest+ask、W5 practice、W6 历史 / 切换模型。
"""

from __future__ import annotations

import typer
from rich.console import Console

app = typer.Typer(
    name="codemate",
    help="CodeMate · AI 学习搭子",
    no_args_is_help=True,
)
console = Console()


@app.command()
def hello(name: str = "world") -> None:
    """Smoke test：W1 第一天确认 CLI 跑通。"""
    console.print(f"[bold cyan]Hello, {name}![/] CodeMate v0.0.1 骨架就绪 ✨")


@app.command()
def version() -> None:
    """打印版本号。"""
    from codemate import __version__
    console.print(f"codemate {__version__}")


# W4 起填充：
# @app.command()
# def ingest(path: Path) -> None: ...
#
# @app.command()
# def ask(question: str) -> None: ...
#
# W5 起填充：
# @app.command()
# def practice(weak: str = typer.Option(...), difficulty: str = "Medium") -> None: ...


if __name__ == "__main__":
    app()
