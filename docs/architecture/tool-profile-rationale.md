# graphics-mcp Tool Profile System

## Context

graphics-mcp is a small FastMCP server (2 register groups, 11 tools) that
needs to follow the Bodai ecosystem-wide convention of gating tool
registration via a `*_TOOL_PROFILE` environment variable. The convention
originates in mcp-common 0.18.0 (`mcp_common.tools.dispatch`) and has been
adopted across W1.1-W1.4 + W2a + W2b.1 + W2b.2 + W2b.3 of the mcp-tool-profile
rollout.

Pre-refactor, `graphics_mcp/server.py::create_app` called the two register
functions directly at startup:

```python
register_universal_tools(app, backend)
register_raster_tools(app, backend)
```

This worked, but had no env-var gating — operators could not reduce the
tool surface for memory-constrained clients or health-probe deployments.

## Decision

graphics-mcp adopts the W0 tool profile dispatch (`_apply_tool_profile`
from `mcp_common.tools.dispatch`) with a **2-tier mapping** (Tier-B
per the W3 brief). The mapping lives in
`graphics_mcp/tools/profiles.py`:

| Profile   | Registered groups         | Total tools |
|-----------|---------------------------|-------------|
| MINIMAL   | (none)                    | 0 + `discover_tools` = 1 |
| FULL      | `universal_tools`, `raster_tools` | 11 + `discover_tools` = 12 |

`STANDARD` is intentionally **omitted** — graphics-mcp has only 2 register
groups and 11 tools; a 3-tier split adds no operational value. Operators
who want fewer tools use `MINIMAL`; operators who want the full surface
use `FULL` (the default). No `STANDARD` middle ground needed.

The env var is `GRAPHICS_TOOL_PROFILE`. Unset / empty / unknown → FULL
(match `mcp_common.tools.ToolProfile.from_env` behavior).

## Wiring

`graphics_mcp/server.py::create_app` is now `async def` and ends with:

```python
await apply_graphics_tool_profile(app)
```

`apply_graphics_tool_profile` (in `graphics_mcp/tools/profiles.py`) is the
async wrapper around `mcp_common.tools.dispatch._apply_tool_profile`. The
sync `apply_tool_profile()` wrapper raises `RuntimeError` inside a running
event loop, so the async path is the only correct entry point for any
async startup context (and for tests that exercise `create_app` under
`asyncio`).

Sync callers (`get_app`, CLI startup) bridge via `asyncio.run(create_app())`.

## Backend instantiation

Both `register_universal_tools` and `register_raster_tools` take a
`(app, backend)` 2-arg signature. The W0 helper expects single-arg
callables (`Callable[[FastMCP], Awaitable[None] | None]`). `_build_registration_map`
and `register_all_tool_groups` both instantiate a single `PillowBackend`
and bind it via a lambda. The backend is stateless (each method opens
and processes an image independently), so a single instance is safe to
share across both groups.

## MANDATORY_TOOLS invariant

graphics-mcp has **no MCP-registered health tools** — only the `/healthz`
HTTP route (registered via `mcp_common.health.register_http_health_route`,
which is a custom Starlette route, not an MCP tool). The
`MANDATORY_GROUPS` / `MANDATORY_TOOLS` invariants from mcp-common are
therefore vacuously satisfied.

`apply_graphics_tool_profile` passes `mandatory_groups=set()` and
`essential_tool_names=set()` explicitly to opt out of the subset check.
`tests/test_tool_profile.py::test_mandatory_tools_invariant` pins this
opt-out via `inspect.getsource` so the relationship cannot drift silently.

## Behavioral parity

| Profile | Pre-refactor (inline) | Post-refactor (W0 helper) | Match? |
|---------|-----------------------|---------------------------|--------|
| (unset) | 11 tools at startup   | 11 + `discover_tools` = 12 | YES (extra discover_tools is by design) |
| MINIMAL | (not supported)        | 0 + `discover_tools` = 1 | NEW behavior |
| FULL    | (always-on)           | 11 + `discover_tools` = 12 | YES |

The 11 graphics tool names are identical at FULL profile to the
pre-refactor inline mode (verified by
`tests/test_tool_profile.py::test_full_registers_all_11_tools`). The W0
helper additionally registers the `discover_tools` meta-tool, which is
the ecosystem-wide convention (matches W1.1-W1.4 + W2a + W2b.1 + W2b.2 +
W2b.3 behavior).

The `/healthz` custom HTTP route is unchanged (registered via
`register_http_health_route(app, ...)`) — it does NOT register an MCP
tool, so it doesn't appear in `list_tools()` (intentional, per W1.4
convention).

## MANDATORY_TOOLS ⊆ REGISTRATION_MAP.keys()

Always true because mcp-common's default `MANDATORY_TOOLS` is empty.
Verified by `test_mandatory_tools_invariant`.

## Files

- `graphics_mcp/tools/profiles.py` (NEW) — `PROFILE_REGISTRATIONS`,
  `_build_registration_map`, `register_all_tool_groups`,
  `apply_graphics_tool_profile`
- `graphics_mcp/server.py` (MODIFIED) — `create_app` now `async def`,
  ends with `await apply_graphics_tool_profile(app)`; `get_app`
  bridges via `asyncio.run`
- `tests/test_tool_profile.py` (NEW) — 17 wiring tests (12 AST + 5 runtime,
  including 2 real production-path tests via `asyncio.run(create_app())`)
- `pyproject.toml` (MODIFIED) — `mcp-common>=0.18.0` pin (was `>=0.17.0`)
- `CLAUDE.md` (MODIFIED) — added "Tool Profile System" subsection

## Test coverage

- 12 AST / static checks (file existence, symbol presence, env var
  reference, AST guards on sync vs async dispatch)
- 5 runtime tests (FULL, MINIMAL, unset-default, invalid-profile, MANDATORY
  invariant)
- 2 real production-path tests via `asyncio.run(create_app())` — one for
  FULL, one for MINIMAL. These tests do NOT mock the dispatch helper
  (per W2b.3 lesson: mock-based tests can mask bugs where the wrong
  sync wrapper is used).

## Notes for downstream consumers

`create_app` is now `async`. Any existing caller that did
`from graphics_mcp.server import create_app; app = create_app()` must
wrap with `asyncio.run`. The `get_app()` singleton bridge handles
the standard `app` / `http_app` access pattern unchanged.

Adding a new tool group requires editing both `FULL_REGISTRATIONS` and
`register_all_tool_groups` (intentional redundancy, matches W2a
Crackerjack pattern).
