# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

For a shorter, tool-neutral bootstrap document, start with `AGENTS.md`.

## Project Overview

**graphics-mcp** is a unified MCP server for graphics manipulation with multiple backends, providing image processing capabilities via the Model Context Protocol.

**Key Dependencies**: Python 3.13+, mcp-common, Pillow/pilkit

## Core Features

- **Image Operations**: Get info, convert, resize, crop, rotate, flip
- **Filters**: Apply effects (blur, sharpen, grayscale, etc.)
- **Thumbnails**: Generate thumbnails with configurable sizes
- **Security**: Path validation, file size limits, allowed directories

## Most Common Commands

```bash
# Start HTTP MCP server (factory default)
graphics-mcp start

# Run local health probe
graphics-mcp health
```

The server is bound via environment variables: `GRAPHICS_HTTP_HOST` and
`GRAPHICS_HTTP_PORT` (defaults `127.0.0.1` and `3040`). Allowed directories are
configured via `GRAPHICS_ALLOWED_DIRECTORIES` (JSON array form, e.g.
`'["/tmp", "/Users/les/Pictures", "/Users/les/Downloads"]'`).

## Critical Rules

### 1. SECURITY IS NON-NEGOTIABLE

- **NEVER** allow arbitrary file paths
- **ALWAYS** validate paths against allowed directories
- **ALWAYS** enforce file size limits
- **NEVER** expose internal filesystem structure

### 2. PATH VALIDATION

- All image paths must be within allowed directories
- Use `GRAPHICS_ALLOWED_DIRECTORIES` environment variable
- Validate before any file operation

### 3. NO PLACEHOLDERS - EVER

- **NEVER** use dummy data orplaceholder images
- **ALWAYS** use proper configuration

### 4. MCP-COMMON PATTERNS

- Follow mcp-common patterns for server lifecycle
- Use MCPServerCLIFactory for CLI commands
- Inherit from base settings classes

## Configuration

Set via environment variables with `GRAPHICS_` prefix:

| Variable | Description | Default |
|----------|-------------|---------|
| `GRAPHICS_ALLOWED_DIRECTORIES` | JSON-array list of allowed paths (e.g. `'["/tmp", "/data"]'`) | - |
| `GRAPHICS_MAX_FILE_SIZE_MB` | Maximum file size | 100 |

## Tools Provided

| Tool | Description |
|------|-------------|
| `get_image_info` | Get image metadata |
| `convert_image` | Convert between formats |
| `resize_image` | Resize with multiple modes |
| `crop_image` | Crop to boundaries |
| `apply_filter` | Apply effects (blur, sharpen, grayscale, etc.) |
| `rotate_image` | Rotate by degrees |
| `flip_image` | Flip horizontally/vertically |
| `create_thumbnail` | Generate thumbnails |

## Tool Profile System

graphics-mcp follows the Bodai ecosystem-wide convention of gating tool
registration via a `*_TOOL_PROFILE` environment variable (mcp-common
0.18.0+). The dispatch surface is in `graphics_mcp/tools/profiles.py`;
the server wires it from `graphics_mcp/server.py::create_app` via
`await apply_graphics_tool_profile(app)`.

| Profile | Env var | Registered groups | Tool count |
|-----------|-------------------------------|----------------------------------|------------|
| FULL | `GRAPHICS_TOOL_PROFILE=full` (default) | `universal_tools`, `raster_tools` | 11 + `discover_tools` = 12 |
| MINIMAL | `GRAPHICS_TOOL_PROFILE=minimal` | (none) | 0 + `discover_tools` = 1 |

`STANDARD` is intentionally omitted (Tier-B 2-tier mapping per the W3
brief). Unset / empty / unknown env var → FULL.

The rationale and design decisions live at
[`docs/architecture/tool-profile-rationale.md`](./docs/architecture/tool-profile-rationale.md).

## Additional Resources

- **[README.md](./README.md)**: Complete project documentation
- **[mcp-common](../mcp-common)**: Shared MCP utilities
