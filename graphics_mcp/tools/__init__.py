"""Graphics tools package."""

from graphics_mcp.tools.raster import register_raster_tools
from graphics_mcp.tools.universal import register_universal_tools

__all__ = ["register_raster_tools", "register_universal_tools"]
