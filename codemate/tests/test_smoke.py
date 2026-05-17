"""最小 smoke test：确保骨架 import 通。"""

from __future__ import annotations


def test_package_imports() -> None:
    import codemate
    from codemate import settings
    from codemate.loaders import base as loaders_base
    from codemate.llm import Message  # noqa: F401
    from codemate.chunkers import Chunk  # noqa: F401

    assert codemate.__version__ == "0.0.1"
    assert hasattr(settings, "settings")
    assert hasattr(loaders_base, "DocumentRecord")


def test_cli_module_imports() -> None:
    from codemate.cli.main import app

    assert app is not None
