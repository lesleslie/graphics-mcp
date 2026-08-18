"""Tool profile registration groups for graphics-mcp MCP server.

Maps ``ToolProfile`` levels to specific ``register_<group>_tools()`` call
lists, controlling which tools are exposed at startup based on the
``GRAPHICS_TOOL_PROFILE`` environment variable.

Profile tiers (2-tier, Tier-B — graphics-mcp is small enough that a
3-tier split adds no value):

    MINIMAL:  No tool groups registered (only ``discover_tools`` meta-tool
              + /healthz HTTP route).
    FULL:     All 11 graphics tools across 2 groups (universal + raster).
              Default behavior — matches pre-refactor inline registration.

The dispatch surface (``PROFILE_REGISTRATIONS`` + ``REGISTRATION_MAP`` +
``register_all_tool_groups`` + ``apply_graphics_tool_profile``) is consumed
by ``graphics_mcp.server.create_app`` which delegates to
``mcp_common.tools.dispatch._apply_tool_profile``.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from mcp_common.tools import ToolProfile
from mcp_common.tools.dispatch import ALL_TOOLS

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from fastmcp import FastMCP

MINIMAL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = []

FULL_REGISTRATIONS: list[str | Callable[[FastMCP], Awaitable[None] | None]] = [
    "universal_tools",
    "raster_tools",
]

PROFILE_REGISTRATIONS: dict[
    ToolProfile,
    list[str | Callable[[FastMCP], Awaitable[None] | None]] | type[ALL_TOOLS],
] = {
    ToolProfile.MINIMAL: MINIMAL_REGISTRATIONS,
    ToolProfile.FULL: FULL_REGISTRATIONS,
}


def _build_registration_map() -> dict[
    str, Callable[[FastMCP], Awaitable[None] | None]
]:
    """Build the {group_key: register_fn(app)} map.

    Local import keeps ``graphics_mcp.tools.profiles`` importable without
    forcing every register_X_tools function in ``graphics_mcp.tools.*`` to
    be resolved at module import time. Called by
    ``apply_graphics_tool_profile`` (not eagerly at import) because
    server.py imports this one at module load.

    Both ``register_universal_tools`` and ``register_raster_tools`` take a
    ``(app, backend)`` signature; the W0 helper expects single-arg
    callables, so this wrapper binds a single shared ``PillowBackend``
    instance at map-build time. The backend is stateless (each method
    opens/processes a file independently) so a single instance is safe
    to share across both groups.
    """
    from graphics_mcp.backends.pillow import PillowBackend
    from graphics_mcp.tools.raster import register_raster_tools
    from graphics_mcp.tools.universal import register_universal_tools

    backend = PillowBackend()
    return {
        "universal_tools": lambda app: register_universal_tools(app, backend),
        "raster_tools": lambda app: register_raster_tools(app, backend),
    }


def register_all_tool_groups(server: FastMCP) -> None:
    """Bulk register every graphics-mcp tool group (called at FULL profile).

    Used as ``register_all_fn`` for the W0 helper. Imports each
    register_<group>_tools directly (not via REGISTRATION_MAP iteration) so
    that adding a new group requires editing both this function and the
    FULL_REGISTRATIONS list — the redundancy is intentional: each is the
    ground-truth for a separate concern (matches W2a Crackerjack pattern).
    """
    from graphics_mcp.backends.pillow import PillowBackend
    from graphics_mcp.tools.raster import register_raster_tools
    from graphics_mcp.tools.universal import register_universal_tools

    backend = PillowBackend()
    register_universal_tools(server, backend)
    register_raster_tools(server, backend)


async def apply_graphics_tool_profile(server: FastMCP) -> None:
    """Apply the GRAPHICS_TOOL_PROFILE dispatch to ``server`` at startup.

    Async because the W0 helper is async; called from
    ``graphics_mcp.server.create_app`` via
    ``await apply_graphics_tool_profile(app)``. The sync ``apply_tool_profile``
    wrapper raises RuntimeError in any async context, so this async path
    is the only correct entry point.

    graphics-mcp exposes no MCP-registered health tools (only the
    /healthz HTTP route via ``mcp_common.health.register_http_health_route``),
    so the MANDATORY_GROUPS / MANDATORY_TOOLS invariants are vacuously
    satisfied. We pass empty sets explicitly to opt out of the subset
    check.
    """
    from mcp_common.tools.dispatch import _apply_tool_profile

    await _apply_tool_profile(
        server,
        profile_env_var="GRAPHICS_TOOL_PROFILE",
        registrations=PROFILE_REGISTRATIONS,
        registration_map=_build_registration_map(),
        register_all_fn=register_all_tool_groups,
        mandatory_groups=set(),
        essential_tool_names=set(),
    )


__all__ = [
    "FULL_REGISTRATIONS",
    "MINIMAL_REGISTRATIONS",
    "PROFILE_REGISTRATIONS",
    "_build_registration_map",
    "apply_graphics_tool_profile",
    "register_all_tool_groups",
]
