"""FastMCP server for graphics manipulation."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from fastmcp import FastMCP

from graphics_mcp import __version__
from graphics_mcp.backends.pillow import PillowBackend
from graphics_mcp.config import get_logger_instance, get_settings, setup_logging
from graphics_mcp.tools import register_raster_tools, register_universal_tools

if TYPE_CHECKING:
    pass

logger = get_logger_instance("graphics-mcp.server")

APP_NAME = "graphics-mcp"
APP_VERSION = __version__


def create_app() -> FastMCP:
    """Create and configure the FastMCP application."""
    settings = get_settings()
    setup_logging(settings)

    logger.info(
        "Initializing graphics-mcp server",
        version=APP_VERSION,
        default_backend=settings.default_backend,
    )

    app = FastMCP(name=APP_NAME, version=APP_VERSION)

    # HTTP health endpoint for Claude Code compatibility
    @app.custom_route("/health", methods=["GET"])
    async def health_check(request: Any) -> Any:
        """HTTP health check endpoint for Claude Code `mcp list` compatibility."""
        from starlette.responses import JSONResponse

        return JSONResponse(
            {"status": "ok", "service": "graphics", "version": APP_VERSION}
        )

    @app.custom_route("/healthz", methods=["GET"])
    async def healthz_check(request: Any) -> Any:
        """Kubernetes-style health check endpoint."""
        from starlette.responses import JSONResponse

        return JSONResponse({"status": "ok"})

    # Initialize backend
    backend = PillowBackend()

    # Register tools
    register_universal_tools(app, backend)
    register_raster_tools(app, backend)

    # Log registered tools
    logger.info(
        "Tools registered",
        universal=[
            "get_image_info",
            "convert_image",
            "list_allowed_directories",
            "list_supported_formats",
        ],
        raster=[
            "resize_image",
            "crop_image",
            "apply_filter",
            "rotate_image",
            "flip_image",
            "create_thumbnail",
            "list_available_filters",
        ],
    )

    return app


_app: FastMCP | None = None


def get_app() -> FastMCP:
    """Get the singleton FastMCP application."""
    global _app
    if _app is None:
        _app = create_app()
    return _app


def __getattr__(name: str) -> Any:
    """Dynamic attribute access for app and http_app."""
    if name == "app":
        return get_app()
    if name == "http_app":
        return get_app().http_app
    raise AttributeError(f"module '{__name__}' has no attribute '{name}'")


__all__ = ["create_app", "get_app", "APP_NAME", "APP_VERSION"]
