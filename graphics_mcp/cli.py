"""Unified CLI for Graphics MCP server using mcp-common.

Provides standard lifecycle commands (start, stop, restart, status, health).
"""

from __future__ import annotations

import os
import warnings

os.environ["TRANSFORMERS_VERBOSITY"] = "error"
warnings.filterwarnings("ignore", message=".*PyTorch.*TensorFlow.*Flax.*")

import uvicorn

from mcp_common import MCPServerCLIFactory, MCPServerSettings
from mcp_common.cli.health import RuntimeHealthSnapshot

from graphics_mcp import __version__


class GraphicsSettings(MCPServerSettings):
    """Graphics MCP server settings extending MCPServerSettings."""

    server_name: str = "graphics-mcp"
    http_port: int = 3040
    startup_timeout: int = 10
    shutdown_timeout: int = 10
    force_kill_timeout: int = 5


def start_server_handler() -> None:
    """Start handler that launches the Graphics MCP server in HTTP mode."""
    settings = GraphicsSettings()
    print(f"Starting Graphics MCP server on port {settings.http_port}...")
    uvicorn.run(
        "graphics_mcp.server:http_app",
        host="127.0.0.1",
        port=settings.http_port,
        log_level="info",
    )


def health_probe_handler() -> RuntimeHealthSnapshot:
    """Health probe handler for Graphics MCP server."""
    from graphics_mcp.config import get_settings

    settings = get_settings()
    return RuntimeHealthSnapshot(
        server_name="graphics-mcp",
        status="healthy",
        version=__version__,
        extra={
            "default_backend": settings.default_backend,
            "pillow_enabled": settings.enable_pillow,
        },
    )


factory = MCPServerCLIFactory(
    server_name="graphics-mcp",
    settings=GraphicsSettings(),
    start_handler=start_server_handler,
    health_probe_handler=health_probe_handler,
)

app = factory.create_app()


def main() -> None:
    """Main entry point."""
    app()


if __name__ == "__main__":
    main()
