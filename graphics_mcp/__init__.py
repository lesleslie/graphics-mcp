"""Graphics MCP - Unified MCP server for graphics manipulation."""

from importlib.metadata import version as _importlib_version

from graphics_mcp.config import GraphicsSettings, get_settings, setup_logging
from graphics_mcp.models import (
    ConvertOptions,
    CropOptions,
    FilterOptions,
    FilterType,
    ImageFormat,
    ImageInfo,
    ResizeMode,
    ResizeOptions,
    ToolResponse,
    TransformResult,
)

__version__ = _importlib_version("graphics-mcp")

__all__ = [
    "GraphicsSettings",
    "get_settings",
    "setup_logging",
    "ConvertOptions",
    "CropOptions",
    "FilterOptions",
    "FilterType",
    "ImageFormat",
    "ImageInfo",
    "ResizeMode",
    "ResizeOptions",
    "ToolResponse",
    "TransformResult",
    "__version__",
]
