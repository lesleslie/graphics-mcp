"""Regression guard: __version__ must mirror the installed distribution.

The graphics-mcp package exposes ``__version__`` via
``importlib.metadata.version("graphics-mcp")`` (see
``graphics_mcp/__init__.py``). This test pins the contract so a
hand-edited literal in ``__init__.py`` cannot silently drift away from
the canonical version declared in ``pyproject.toml`` (the source of
truth that crackerjack bumps on every release).
"""

from __future__ import annotations

from importlib.metadata import version

from graphics_mcp import __version__


def test_version_sync() -> None:
    """``graphics_mcp.__version__`` must equal the installed dist version."""
    dist_version = version("graphics-mcp")
    assert __version__ == dist_version, (
        f"__version__ ({__version__}) drifted from pyproject ({dist_version}). "
        "graphics_mcp/__init__.py must load __version__ from importlib.metadata."
    )
