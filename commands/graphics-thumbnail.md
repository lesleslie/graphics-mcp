---
description: Create a bounded thumbnail from a source image, capped at the supplied width and height.
argument-hint: <image-path> [--width N] [--height N]
allowed-tools: mcp__graphics__create_thumbnail, mcp__graphics__list_allowed_directories, mcp__graphics__get_image_info
---

# /graphics-thumbnail

Create a thumbnail for a source image, bounded by the supplied maximum width and height.

## Usage

`/graphics-thumbnail <image-path> [--width N] [--height N]`

Arguments:

- `<image-path>`: absolute path to the source image. Must be under a directory returned by `mcp__graphics__list_allowed_directories`.
- `--width N`: optional maximum thumbnail width in pixels. Defaults are applied by the MCP server when omitted.
- `--height N`: optional maximum thumbnail height in pixels. Defaults are applied by the MCP server when omitted.

The thumbnail is bounded: it never exceeds the supplied dimensions and never upscales beyond the source size.

## Workflow

1. Call `mcp__graphics__list_allowed_directories` to confirm the source path is allowed.
2. Call `mcp__graphics__get_image_info` to record the original dimensions for the report.
3. Call `mcp__graphics__create_thumbnail` with `image_path`, `width`, and `height`.
4. Report the output path and the thumbnail dimensions.

## Example

`/graphics-thumbnail /Users/les/Pictures/photo.png --width 256 --height 256`
