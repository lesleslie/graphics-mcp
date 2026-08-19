---
description: Resize an image by width and/or height with a fit/fill/exact mode (default mode=fit).
argument-hint: <image-path> [--width N] [--height N] [--mode fit|fill|exact]
allowed-tools: mcp__graphics__resize_image, mcp__graphics__list_allowed_directories, mcp__graphics__get_image_info
---

# /graphics-resize

Resize an image while preserving aspect ratio (default mode) or forcing exact dimensions.

## Usage

`/graphics-resize <image-path> [--width N] [--height N] [--mode fit|fill|exact]`

Arguments:

- `<image-path>`: absolute path to the source image. Must be under a directory returned by `mcp__graphics__list_allowed_directories`.
- `--width N`: optional target width in pixels. Provide either `--width` or `--height` (or both for `--mode exact`).
- `--height N`: optional target height in pixels.
- `--mode`: resize mode. `fit` (default) preserves aspect ratio and fits within the bounding box. `fill` preserves aspect ratio and crops to fill. `exact` forces the exact target dimensions.

## Workflow

1. Call `mcp__graphics__list_allowed_directories` to confirm the source path is allowed.
2. Call `mcp__graphics__get_image_info` to record the original dimensions and mode for the report.
3. Call `mcp__graphics__resize_image` with `image_path`, `width`, `height`, and `mode` (default `fit`).
4. Report the new dimensions and the output path.

## Example

`/graphics-resize /Users/les/Pictures/photo.png --width 1024 --mode fit`
