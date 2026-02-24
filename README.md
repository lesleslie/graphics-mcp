# graphics-mcp

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
