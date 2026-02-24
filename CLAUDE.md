# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with this repository.

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
# Run server (stdio mode)
graphics-mcp serve

# Run server (HTTP mode)
graphics-mcp serve --http --port 3040

# With custom allowed directories
graphics-mcp serve --allowed-dir /path/to/images
```

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
| `GRAPHICS_ALLOWED_DIRECTORIES` | Comma-separated list of allowed paths | - |
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

## Additional Resources

- **[README.md](./README.md)**: Complete project documentation
- **[mcp-common](../mcp-common)**: Shared MCP utilities
