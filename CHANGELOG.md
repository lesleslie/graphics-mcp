# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.4.0] - 2026-08-28

### Documentation

- readme: Bump Python badge from 3.13+ to 3.14+

### Internal

- Bump requires-python to >=3.14
- graphics-mcp: Bump tool-config pins from 3.13 to 3.14
- graphics-mcp: Uv python pin 3.14

## [0.3.0] - 2026-08-20

### Added

- graphics-mcp: Adopt apply_tool_profile with GRAPHICS_TOOL_PROFILE
- graphics-mcp: Bodai plugin conversion (manifest, mcp.json, slash commands)

### Fixed

- graphics-mcp: Ruff cleanup (F401, I001, SIM102)

### Internal

- gitignore: Untrack .pyscn/ (bodai 2026-08-20)
- graphics-mcp: Add [tool.creosote] to skip self-tool scan
- graphics-mcp: Bootstrap [tool.crackerjack] section + uv sync upgrade
- graphics-mcp: Gitignore .lycheecache (file, not just dir)
- graphics-mcp: Gitignore .lycheecache + .hypothesis
- graphics-mcp: Refresh oneiric + mcp-common deps
- graphics-mcp: Untrack .lycheecache + .hypothesis runtime artifacts

## [0.2.1] - 2026-08-14

### Documentation

- Fix version drift, CLI surface, env vars, and FastMCP badge URL

### Internal

- Untrack backup files (.backup, .backup.json, .bak)

## [0.2.0] - 2026-08-12

### Fixed

- Address crackerjack ty errors

### Internal

- Adopt register_http_health_route from mcp-common
- Bump oneiric dep to >=0.16.0
- Migrate MCPBaseSettings → OneiricMCPConfig, bump fastmcp to >=3.4.0,\<4

## [0.1.3] - 2026-06-19

### Changed

- Graphics-mcp (quality: 53/100) - 2026-06-19 02:07:09

### Internal

- Untrack and delete 1 historical *.backup/*.bak files
