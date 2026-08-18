"""FastMCP server for graphics manipulation."""

from __future__ import annotations

import asyncio
from typing import TYPE_CHECKING, Any

from mcp_common.fastmcp import FastMCP
from mcp_common.health import register_http_health_route

from graphics_mcp import __version__
from graphics_mcp.config import get_logger_instance, get_settings, setup_logging
from graphics_mcp.tools.profiles import apply_graphics_tool_profile

if TYPE_CHECKING:
    pass

logger = get_logger_instance("graphics-mcp.server")

APP_NAME = "graphics-mcp"
APP_VERSION = __version__


async def create_app() -> FastMCP:
    """Create and configure the FastMCP application (async).

    Tool profile dispatch is async because the W0 helper from
    mcp-common 0.18.0 (``_apply_tool_profile``) is async. Per the
    W1.4 + W2a + W2b.1 + W2b.3 lessons, the sync ``apply_tool_profile``
    wrapper raises ``RuntimeError`` when called from inside a running
    event loop, so the async path is the only correct path for both
    production code and any integration that runs inside an asyncio loop.

    Callers from sync contexts (CLI startup, ``get_app``) wrap with
    ``asyncio.run(create_app())``.
    """
    settings = get_settings()
    setup_logging(settings)

    logger.info(
        "Initializing graphics-mcp server",
        version=APP_VERSION,
        default_backend=settings.default_backend,
    )

    app = FastMCP(name=APP_NAME, version=APP_VERSION)

    register_http_health_route(app, service_name="graphics", version=APP_VERSION)

    @app.custom_route("/healthz", methods=["GET"])
    async def healthz_check(request: Any) -> Any:
        """Kubernetes-style health check endpoint."""
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok"})

    # Apply tool profile dispatch (GRAPHICS_TOOL_PROFILE env var).
    #
    # Replaces the previous direct register_*_tools(app, backend) calls.
    # The W0 helper from mcp-common 0.18.0+ dispatches by group name and
    # always registers the ``discover_tools`` meta-tool. The default (no
    # env var) remains FULL = all 11 tools — the previous behavior is
    # preserved.
    await apply_graphics_tool_profile(app)

    return app


_app: FastMCP | None = None


def get_app() -> FastMCP:
    """Get the singleton FastMCP application (sync wrapper).

    Bridges to the async ``create_app`` via ``asyncio.run``. This works
    because the FastMCP app-building phase does not require a running
    event loop — only the tool profile dispatch needs an async context.
    """
    global _app
    if _app is None:
        _app = asyncio.run(create_app())
    return _app


def __getattr__(name: str) -> Any:
    """Dynamic attribute access for app and http_app."""
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["create_app", "get_app", "APP_NAME", "APP_VERSION"]
