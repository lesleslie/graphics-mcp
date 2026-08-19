---
description: Convert an image to JPEG/PNG/GIF/BMP/WEBP/TIFF with optional quality and optimization.
argument-hint: <image-path> <target-format> [--quality N] [--optimize]
allowed-tools: mcp__graphics__convert_image, mcp__graphics__list_allowed_directories, mcp__graphics__list_supported_formats, mcp__graphics__get_image_info
---

# /graphics-convert

Convert an image to a different format using the graphics MCP server.

## Usage

`/graphics-convert <image-path> <target-format> [--quality N] [--optimize]`

Arguments:

- `<image-path>`: absolute path to the source image file. Must be under one of the directories returned by `mcp__graphics__list_allowed_directories`.
- `<target-format>`: one of the formats returned by `mcp__graphics__list_supported_formats` (typically `jpeg`, `png`, `gif`, `bmp`, `webp`, `tiff`).
- `--quality N`: optional, integer 1-100. Used for lossy targets (JPEG/WEBP).
- `--optimize`: optional flag. Enables format-specific size optimization.

## Workflow

1. Call `mcp__graphics__list_allowed_directories` to confirm `<image-path>` is under a permitted root.
2. Call `mcp__graphics__list_supported_formats` to validate the requested `<target-format>`.
3. Call `mcp__graphics__get_image_info` with `<image-path>` to capture source dimensions and metadata for the report.
4. Call `mcp__graphics__convert_image` with `image_path`, `output_format`, and any optional flags.
5. Report the output path and the size delta (source bytes vs. converted bytes).

## Example

`/graphics-convert /Users/les/Pictures/photo.png webp --quality 85 --optimize`
