# graphics-mcp

[![Code style: crackerjack](https://img.shields.io/badge/code%20style-crackerjack-000042)](https://github.com/lesleslie/crackerjack)
[![Runtime: oneiric](https://img.shields.io/badge/runtime-oneiric-6e5494)](https://github.com/lesleslie/oneiric)
[![Framework: FastMCP](https://img.shields.io/badge/framework-FastMCP-0ea5e9)](https://github.com/jlowin/fastmcp)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Python: 3.13+](https://img.shields.io/badge/python-3.13%2B-green)](https://www.python.org/downloads/)

Unified MCP server for graphics manipulation with multiple backends.

## Installation

```bash
uv pip install -e .
```

## Usage

```bash
# Stdio mode (default)
graphics-mcp serve

# HTTP mode
graphics-mcp serve --http --port 3040

# With custom allowed directories
graphics-mcp serve --allowed-dir /path/to/images
```

## Tools

- `get_image_info` - Get image metadata
- `convert_image` - Convert between formats
- `resize_image` - Resize with multiple modes
- `crop_image` - Crop to boundaries
- `apply_filter` - Apply effects (blur, sharpen, grayscale, etc.)
- `rotate_image` - Rotate by degrees
- `flip_image` - Flip horizontally/vertically
- `create_thumbnail` - Generate thumbnails

## Configuration

Set via environment variables with `GRAPHICS_` prefix:

- `GRAPHICS_ALLOWED_DIRECTORIES` - Comma-separated list of allowed paths
- `GRAPHICS_MAX_FILE_SIZE_MB` - Maximum file size (default: 100)
