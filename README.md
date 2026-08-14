# Graphics MCP Server

[![Code style: crackerjack](https://img.shields.io/badge/code%20style-crackerjack-000042)](https://github.com/lesleslie/crackerjack)
[![Runtime: oneiric](https://img.shields.io/badge/runtime-oneiric-6e5494)](https://github.com/lesleslie/oneiric)
[![Framework: FastMCP](https://img.shields.io/badge/framework-FastMCP-0ea5e9)](https://github.com/PrefectHQ/fastmcp)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python: 3.13+](https://img.shields.io/badge/python-3.13%2B-green)](https://www.python.org/downloads/)

Unified MCP server for raster image inspection, conversion, and manipulation.

**Version:** 0.2.0
**Status:** Internal Bodai integration component

## Quick Links

- [Overview](#overview)
- [Capabilities](#capabilities)
- [Quick Start](#quick-start)
- [MCP Server Configuration](#mcp-server-configuration)
- [Tool Reference](#tool-reference)
- [Configuration](#configuration)
- [Development](#development)

## Quality & CI

Crackerjack is the standard quality-control and CI/CD gate for Graphics MCP changes. Local verification should mirror the Crackerjack workflow used across the Bodai ecosystem.

______________________________________________________________________

## Overview

Graphics MCP exposes common image operations through a FastMCP server. It gives agents a bounded way to inspect image metadata, convert formats, resize, crop, rotate, flip, thumbnail, and apply filters while keeping filesystem access constrained to configured directories.

The current implementation uses the Pillow backend. The settings model already reserves flags for ImageMagick and GIMP backends, but those should be treated as future or optional surfaces unless validated for the target deployment.

## Capabilities

Implemented tool surface:

- **Image inspection**: read dimensions, format, mode, and file metadata
- **Format conversion**: convert among JPEG, PNG, GIF, BMP, WEBP, and TIFF
- **Resize and crop**: fit, fill, exact, and crop-oriented raster transformations
- **Filter operations**: blur, sharpen, grayscale, sepia, invert, contrast, brightness, and related effects
- **Orientation operations**: rotate and flip images
- **Thumbnail generation**: create bounded thumbnails from source images
- **Filesystem guardrails**: list and enforce configured allowed directories and maximum file size
- **HTTP health routes**: `/health` and `/healthz` for MCP client and process supervision checks

## Quick Start

### Prerequisites

- Python 3.13+
- UV package manager
- Local image files under an allowed directory

### Local Setup

```bash
git clone https://github.com/lesleslie/graphics-mcp.git
cd graphics-mcp
uv sync --group dev
```

### Run The Server

```bash
uv run graphics-mcp start
uv run graphics-mcp health
```

The default HTTP bind is `127.0.0.1:3040`.

### Allow A Working Directory

```bash
export GRAPHICS_ALLOWED_DIRECTORIES="/tmp,/Users/les/Pictures,/Users/les/Downloads"
uv run graphics-mcp start
```

## CLI Commands

The CLI is built with `mcp-common` and provides the standard lifecycle command surface used by Bodai MCP servers.

```bash
uv run graphics-mcp start      # Start the HTTP MCP server
uv run graphics-mcp stop       # Stop the managed server process
uv run graphics-mcp restart    # Restart the managed server process
uv run graphics-mcp status     # Show process status
uv run graphics-mcp health     # Run the local health probe
```

## MCP Server Configuration

### Claude / Codex Style Configuration

Add the server to an MCP client configuration:

```json
{
  "mcpServers": {
    "graphics": {
      "command": "uv",
      "args": ["run", "graphics-mcp", "start"],
      "cwd": "/Users/les/Projects/graphics-mcp",
      "env": {
        "GRAPHICS_ALLOWED_DIRECTORIES": "[\"/tmp\", \"/Users/les/Pictures\", \"/Users/les/Downloads\"]"
      }
    }
  }
}
```

### Health Checks

```bash
curl http://127.0.0.1:3040/health
curl http://127.0.0.1:3040/healthz
```

## Tool Reference

| Tool | Purpose | Key Inputs |
|------|---------|------------|
| `get_image_info` | Inspect image metadata | `image_path` |
| `convert_image` | Convert an image to another format | `image_path`, `output_format` |
| `resize_image` | Resize an image by width, height, and mode | `image_path` (required); `width` XOR `height` |
| `crop_image` | Crop an image to pixel boundaries | `image_path`, `left`, `top`, `right`, `bottom` |
| `apply_filter` | Apply a raster filter effect | `image_path`, `filter_type` |
| `rotate_image` | Rotate an image by degrees | `image_path`, `degrees` |
| `flip_image` | Flip horizontally or vertically | `image_path` |
| `create_thumbnail` | Create a thumbnail within max dimensions | `image_path`, `width`, `height` |
| `list_available_filters` | List supported filter names | none |
| `list_allowed_directories` | Show configured filesystem guardrails | none |
| `list_supported_formats` | Show supported image formats | none |

Tool responses follow a consistent `ToolResponse` shape:

```json
{
  "success": true,
  "message": "Image converted successfully",
  "data": {},
  "error": null,
  "next_steps": []
}
```

## Configuration

Committed defaults live in `settings/graphics.yaml`. Runtime overrides should come from environment variables or a local `.env` file that is not committed.

| Setting | Environment Variable | Default |
|---------|----------------------|---------|
| Default backend | `GRAPHICS_DEFAULT_BACKEND` | `pillow` |
| Enable Pillow | `GRAPHICS_ENABLE_PILLOW` | `true` |
| Enable ImageMagick | `GRAPHICS_ENABLE_IMAGEMAGICK` | `false` |
| Enable GIMP | `GRAPHICS_ENABLE_GIMP` | `false` |
| Allowed directories | `GRAPHICS_ALLOWED_DIRECTORIES` | `/tmp`, `~/Pictures`, `~/Downloads` |
| Max file size | `GRAPHICS_MAX_FILE_SIZE_MB` | `100` |
| Allowed formats | `GRAPHICS_ALLOWED_FORMATS` | `JPEG`, `PNG`, `GIF`, `BMP`, `WEBP`, `TIFF` |
| Enable HTTP transport | `GRAPHICS_ENABLE_HTTP_TRANSPORT` | `false` |
| HTTP host | `GRAPHICS_HTTP_HOST` | `127.0.0.1` |
| HTTP port | `GRAPHICS_HTTP_PORT` | `3040` |
| Log level | `GRAPHICS_LOG_LEVEL` | `INFO` |
| JSON logs | `GRAPHICS_LOG_JSON` | `true` |

## Project Structure

```text
graphics_mcp/
  backends/          # Backend interface and Pillow implementation
  cli.py             # mcp-common lifecycle CLI
  config.py          # Pydantic settings and logging
  models.py          # Typed image operation models
  server.py          # FastMCP application factory
  tools/             # Universal and raster MCP tools
settings/
  graphics.yaml      # Committed defaults
tests/
```

## Development

```bash
uv sync --group dev
uv run pytest
uv run ruff check graphics_mcp tests
uv run ruff format graphics_mcp tests
uv run mypy graphics_mcp
```

Use targeted tests when isolating a backend or tool behavior:

```bash
uv run pytest tests -k resize -v
```

## Security Notes

- Keep image file access constrained with `GRAPHICS_ALLOWED_DIRECTORIES`.
- Do not add tools that write outside configured paths.
- Treat user-provided image paths as untrusted input.
- Avoid logging full sensitive local paths when examples are shared outside local development.
