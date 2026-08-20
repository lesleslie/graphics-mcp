"""graphics-mcp tool profile wiring tests.

Verifies the W3.1 adoption of ``mcp_common.tools.dispatch._apply_tool_profile``
replaces the inline 2 ``register_*_tools(app, backend)`` calls with a
2-tier callable-mode architecture (MINIMAL / FULL) gated by the
``GRAPHICS_TOOL_PROFILE`` environment variable.
"""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_profiles_py_exists() -> None:
    """profiles.py must exist under graphics_mcp/tools/."""
    profiles = REPO_ROOT / "graphics_mcp" / "tools" / "profiles.py"
    assert profiles.exists(), f"{profiles} missing"


def test_profiles_py_defines_profile_registrations() -> None:
    """profiles.py must export a PROFILE_REGISTRATIONS dict."""
    profiles = REPO_ROOT / "graphics_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = False
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(
            isinstance(t, ast.Name) and t.id == "PROFILE_REGISTRATIONS"
            for t in node.targets
        ):
            found = True
            break
        if (
            isinstance(node, ast.AnnAssign)
            and isinstance(node.target, ast.Name)
            and node.target.id == "PROFILE_REGISTRATIONS"
        ):
            found = True
            break
    assert found, "PROFILE_REGISTRATIONS not defined in profiles.py"


def test_profiles_py_defines_build_registration_map() -> None:
    """profiles.py must export ``_build_registration_map`` (consumed by apply_graphics_tool_profile)."""
    profiles = REPO_ROOT / "graphics_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "_build_registration_map"
        for node in ast.walk(tree)
    )
    assert found, "_build_registration_map not defined in profiles.py"


def test_profiles_py_defines_register_all_tool_groups() -> None:
    """profiles.py must export ``register_all_tool_groups`` (used as register_all_fn at FULL profile)."""
    profiles = REPO_ROOT / "graphics_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
        and node.name == "register_all_tool_groups"
        for node in ast.walk(tree)
    )
    assert found, "register_all_tool_groups not defined in profiles.py"


def test_profiles_py_defines_apply_graphics_tool_profile() -> None:
    """profiles.py must export ``apply_graphics_tool_profile`` (async wrapper)."""
    profiles = REPO_ROOT / "graphics_mcp" / "tools" / "profiles.py"
    tree = ast.parse(profiles.read_text())
    found = any(
        isinstance(node, ast.AsyncFunctionDef)
        and node.name == "apply_graphics_tool_profile"
        for node in ast.walk(tree)
    )
    assert found, "apply_graphics_tool_profile (async) not defined in profiles.py"


def test_profiles_py_references_graphics_tool_profile_env_var() -> None:
    """GRAPHICS_TOOL_PROFILE env var must be referenced in profiles.py."""
    profiles = REPO_ROOT / "graphics_mcp" / "tools" / "profiles.py"
    text = profiles.read_text()
    assert "GRAPHICS_TOOL_PROFILE" in text, (
        "GRAPHICS_TOOL_PROFILE env var not referenced in profiles.py"
    )


def test_server_uses_async_create_app() -> None:
    """server.py must have an ``async def create_app`` so it can await the dispatch helper."""
    server = REPO_ROOT / "graphics_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    found = any(
        isinstance(node, ast.AsyncFunctionDef) and node.name == "create_app"
        for node in ast.walk(tree)
    )
    assert found, "async def create_app not found in server.py"


def test_server_awaits_apply_graphics_tool_profile() -> None:
    """server.py must ``await apply_graphics_tool_profile(app)`` (the async wrapper).

    Per the W1.4 + W2a + W2b.1 + W2b.3 lessons: the production path must use
    the async helper, NOT the sync wrapper. The sync wrapper raises
    ``RuntimeError`` when called from inside a running event loop, which
    would break any test that runs ``create_app`` under an async context.
    """
    server = REPO_ROOT / "graphics_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    found = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Await):
            continue
        if not isinstance(node.value, ast.Call):
            continue
        if not (
            isinstance(node.value.func, ast.Name)
            and node.value.func.id == "apply_graphics_tool_profile"
        ):
            continue
        found = True
        break
    assert found, "await apply_graphics_tool_profile(app) not found in server.py"


def test_server_does_not_use_sync_wrapper() -> None:
    """server.py must NOT call the sync ``apply_tool_profile`` wrapper.

    W2b.3 round-1 review fix: the sync wrapper raises RuntimeError in
    event loops. The production path must use the async
    ``apply_graphics_tool_profile`` defined in profiles.py.

    Also catches accidental imports of the sync wrapper — the helper is
    only safe at module import time when no event loop is running.
    """
    server = REPO_ROOT / "graphics_mcp" / "server.py"
    tree = ast.parse(server.read_text())
    sync_call = False
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        if isinstance(node.func, ast.Name) and node.func.id == "apply_tool_profile":
            sync_call = True
    assert not sync_call, (
        "server.py must NOT call the sync apply_tool_profile() wrapper "
        "(raises RuntimeError in event loops). Use apply_graphics_tool_profile "
        "instead."
    )


def test_server_no_inline_register_calls() -> None:
    """server.py must NOT call register_universal_tools or register_raster_tools directly.

    Those calls must be routed through the W0 dispatch helper so the
    profile env var controls which groups register.
    """
    server = REPO_ROOT / "graphics_mcp" / "server.py"
    text = server.read_text()
    for fn in ("register_universal_tools", "register_raster_tools"):
        assert fn not in text, (
            f"server.py must not call {fn}() directly; "
            f"route through apply_graphics_tool_profile(app) instead."
        )


def test_pyproject_bumps_mcp_common_to_0_18() -> None:
    """mcp-common pin must be >=0.18.0 (the W0 helper version)."""
    pyproject = REPO_ROOT / "pyproject.toml"
    text = pyproject.read_text()
    assert "mcp-common>=0.18.0" in text, (
        "mcp-common pin must be >=0.18.0 in pyproject.toml"
    )


def test_decision_doc_exists_at_tracked_path() -> None:
    """Rationale doc must live at docs/architecture/tool-profile-rationale.md (.claude/ is gitignored)."""
    path = REPO_ROOT / "docs" / "architecture" / "tool-profile-rationale.md"
    assert path.exists(), f"{path} missing"


def test_profile_registrations_subset_of_map() -> None:
    """Every key referenced in PROFILE_REGISTRATIONS must exist in REGISTRATION_MAP.

    Inline assertion (per W2b.1 lesson: prefer inline ``assert set == {...}``
    over golden fixtures for parity tests).
    """

    from graphics_mcp.tools.profiles import (
        PROFILE_REGISTRATIONS,
        _build_registration_map,
    )

    mapping = _build_registration_map()
    for profile, regs in PROFILE_REGISTRATIONS.items():
        for group in regs:
            if not isinstance(group, str):
                continue
            assert group in mapping, (
                f"{profile.value} references group {group!r} but REGISTRATION_MAP "
                f"is missing it; keys={sorted(mapping)}"
            )


def test_profile_registrations_has_2_tiers() -> None:
    """PROFILE_REGISTRATIONS must have exactly MINIMAL + FULL (Tier-B 2-tier mapping).

    Per the W3 brief: graphics-mcp is Tier-B and uses a 2-tier mapping.
    STANDARD is intentionally absent (3-tier adds no value for a 2-group
    repo with no health tools).
    """
    from mcp_common.tools import ToolProfile

    from graphics_mcp.tools.profiles import PROFILE_REGISTRATIONS

    assert set(PROFILE_REGISTRATIONS.keys()) == {
        ToolProfile.MINIMAL,
        ToolProfile.FULL,
    }, (
        f"PROFILE_REGISTRATIONS must have exactly MINIMAL + FULL; "
        f"got {sorted(PROFILE_REGISTRATIONS.keys())}"
    )


def test_mandatory_tools_invariant() -> None:
    """MANDATORY_TOOLS ⊆ REGISTRATION_MAP.keys() must hold.

    graphics-mcp has NO MCP-registered health tools (only the /healthz HTTP
    route via mcp_common.health), so the MANDATORY_TOOLS invariant is
    vacuously satisfied (mcp-common's default MANDATORY_TOOLS is empty).

    This test pins the explicit opt-out so the relationship cannot drift
    silently:
    - MANDATORY_TOOLS from mcp-common is empty by default
    - apply_graphics_tool_profile passes mandatory_groups=set()
    - apply_graphics_tool_profile passes essential_tool_names=set()

    If any of these change, this test must be updated to reflect the
    new invariant (either add the health tools to REGISTRATION_MAP or
    document the opt-out in the rationale doc).
    """
    import inspect

    from mcp_common.tools.profiles import MANDATORY_TOOLS

    from graphics_mcp.tools.profiles import (
        _build_registration_map,
        apply_graphics_tool_profile,
    )

    mapping = _build_registration_map()
    # Vacuous: MANDATORY_TOOLS empty, so any subset holds
    assert MANDATORY_TOOLS.issubset(set(mapping.keys())), (
        f"MANDATORY_TOOLS {sorted(MANDATORY_TOOLS)} not in REGISTRATION_MAP "
        f"keys {sorted(mapping.keys())}"
    )

    # Verify the explicit opt-out is documented in the implementation
    source = inspect.getsource(apply_graphics_tool_profile)
    assert "mandatory_groups=set()" in source, (
        "apply_graphics_tool_profile must pass mandatory_groups=set() to "
        "explicitly opt out of the MANDATORY_GROUPS invariant"
    )
    assert "essential_tool_names=set()" in source, (
        "apply_graphics_tool_profile must pass essential_tool_names=set() to "
        "explicitly opt out of the MANDATORY_TOOLS subset check"
    )


@pytest.mark.asyncio
async def test_full_registers_all_11_tools(monkeypatch: pytest.MonkeyPatch) -> None:
    """FULL profile must register all 11 graphics tools + discover_tools = 12 total.

    Behavioral parity: original inline registration registered 11 tools.
    The W0 helper additionally registers ``discover_tools`` (the meta-tool
    the W2b.3 spec requires).
    """
    monkeypatch.setenv("GRAPHICS_TOOL_PROFILE", "full")
    from fastmcp import FastMCP

    from graphics_mcp.tools.profiles import apply_graphics_tool_profile

    server = FastMCP(name="Test", instructions="test")
    await apply_graphics_tool_profile(server)
    names = {t.name for t in await server.list_tools()}

    expected_graphics = {
        # universal (4)
        "get_image_info",
        "convert_image",
        "list_allowed_directories",
        "list_supported_formats",
        # raster (7)
        "resize_image",
        "crop_image",
        "apply_filter",
        "rotate_image",
        "flip_image",
        "create_thumbnail",
        "list_available_filters",
    }
    assert expected_graphics.issubset(names), (
        f"FULL profile missing tools: {sorted(expected_graphics - names)}"
    )
    assert "discover_tools" in names, "W0 helper must register discover_tools meta-tool"
    assert len(names) == 12, (
        f"Expected 12 (11 + discover_tools); got {len(names)}: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_full_default_when_unset(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """No GRAPHICS_TOOL_PROFILE env var must default to FULL (matches pre-refactor)."""
    monkeypatch.delenv("GRAPHICS_TOOL_PROFILE", raising=False)
    from fastmcp import FastMCP

    from graphics_mcp.tools.profiles import apply_graphics_tool_profile

    server = FastMCP(name="Test", instructions="test")
    await apply_graphics_tool_profile(server)
    names = {t.name for t in await server.list_tools()}

    assert "get_image_info" in names, "FULL default missing get_image_info"
    assert "resize_image" in names, "FULL default missing resize_image"
    assert "discover_tools" in names


@pytest.mark.asyncio
async def test_minimal_has_only_discover_tools(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """MINIMAL profile registers only ``discover_tools`` (no graphics domain tools)."""
    monkeypatch.setenv("GRAPHICS_TOOL_PROFILE", "minimal")
    from fastmcp import FastMCP

    from graphics_mcp.tools.profiles import apply_graphics_tool_profile

    server = FastMCP(name="Test", instructions="test")
    await apply_graphics_tool_profile(server)
    names = {t.name for t in await server.list_tools()}

    assert names == {"discover_tools"}, (
        f"MINIMAL must only register discover_tools; got: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_invalid_profile_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    """An invalid profile value must raise InvalidProfileError (fail-loud)."""
    from mcp_common.tools.dispatch import InvalidProfileError

    from graphics_mcp.tools.profiles import apply_graphics_tool_profile

    monkeypatch.setenv("GRAPHICS_TOOL_PROFILE", "bogus")
    from fastmcp import FastMCP

    server = FastMCP(name="Test", instructions="test")
    with pytest.raises(InvalidProfileError):
        await apply_graphics_tool_profile(server)


@pytest.mark.asyncio
async def test_create_app_full_profile_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production-path test: exercise the real ``create_app`` async startup.

    This test does NOT mock the dispatch helper (per W2b.3 lesson: mock-based
    tests can mask bugs where the wrong sync wrapper is used). It awaits
    ``create_app()`` directly in the test's event loop and verifies the
    actual tool set.

    If the production path ever uses the sync ``apply_tool_profile()`` wrapper
    (which raises RuntimeError in event loops), this test will fail because
    ``create_app`` is now ``async def`` and the sync wrapper raises before
    the registration can complete.
    """
    from fastmcp import FastMCP

    monkeypatch.setenv("GRAPHICS_TOOL_PROFILE", "full")
    from graphics_mcp.server import create_app

    app: FastMCP = await create_app()
    names = {t.name for t in await app.list_tools()}

    # All 11 graphics tools + discover_tools = 12
    assert "get_image_info" in names
    assert "resize_image" in names
    assert "create_thumbnail" in names
    assert "discover_tools" in names
    assert len(names) == 12, (
        f"Real production path expected 12 tools; got {len(names)}: {sorted(names)}"
    )


@pytest.mark.asyncio
async def test_create_app_minimal_profile_real_path(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Production-path test: MINIMAL profile via the real ``create_app`` async startup."""
    from fastmcp import FastMCP

    monkeypatch.setenv("GRAPHICS_TOOL_PROFILE", "minimal")
    from graphics_mcp.server import create_app

    app: FastMCP = await create_app()
    names = {t.name for t in await app.list_tools()}

    # Only discover_tools under MINIMAL
    assert names == {"discover_tools"}, (
        f"Real production MINIMAL must only register discover_tools; "
        f"got: {sorted(names)}"
    )
