"""Unit tests for ``graphics_mcp.cli``.

Covers the testable pieces of the CLI module:
- ``GraphicsSettings`` defaults
- ``health_probe_handler`` (reads settings, returns RuntimeHealthSnapshot)

The CLI bootstrap (``factory``, ``app``, ``main``, ``__main__`` guard) and
``start_server_handler`` (which calls ``uvicorn.run``) are pragma'd at
the source — they're entry points exercised by crackerjack integration
smoke tests, not unit tests.
"""

from __future__ import annotations

import json

import pytest

from graphics_mcp.cli import GraphicsSettings, health_probe_handler
from graphics_mcp.config import get_settings


@pytest.fixture(autouse=True)
def _reset_settings_cache(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clear the lru_cache on get_settings before and after each test."""
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


class TestGraphicsSettingsDefaults:
    """``GraphicsSettings`` inherits from OneiricMCPConfig with overrides."""

    def test_default_server_name(self) -> None:
        s = GraphicsSettings()

        assert s.server_name == "graphics-mcp"

    def test_default_http_port(self) -> None:
        s = GraphicsSettings()

        assert s.http_port == 3040

    def test_default_lifecycle_timeouts(self) -> None:
        s = GraphicsSettings()

        assert s.startup_timeout == 10
        assert s.shutdown_timeout == 10
        assert s.force_kill_timeout == 5


class TestHealthProbeHandler:
    """``health_probe_handler`` returns a RuntimeHealthSnapshot."""

    def test_returns_snapshot_with_settings(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        # Override settings so the snapshot has known values
        monkeypatch.setenv(
            "GRAPHICS_DEFAULT_BACKEND", "pillow"
        )
        monkeypatch.setenv("GRAPHICS_ENABLE_PILLOW", "true")

        snapshot = health_probe_handler()

        assert snapshot.orchestrator_pid > 0
        assert snapshot.watchers_running is True
        assert snapshot.lifecycle_state["default_backend"] == "pillow"
        assert snapshot.lifecycle_state["pillow_enabled"] is True

    def test_uses_disabled_pillow_setting(
        self, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("GRAPHICS_ENABLE_PILLOW", "false")

        snapshot = health_probe_handler()

        assert snapshot.lifecycle_state["pillow_enabled"] is False


class TestCliBootstrap:
    """The CLI factory/app bootstrap is pragma'd; verify the module loads."""

    def test_module_loads_without_error(self) -> None:
        # Importing the module triggers the factory construction; if any
        # pragma'd line were a real syntax error the import would fail.
        import graphics_mcp.cli  # noqa: F401

        assert graphics_mcp.cli.GraphicsSettings is GraphicsSettings
        assert graphics_mcp.cli.health_probe_handler is health_probe_handler
