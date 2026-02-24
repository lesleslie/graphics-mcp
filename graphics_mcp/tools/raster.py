"""Raster graphics tools for MCP server."""

from __future__ import annotations

from typing import Any

from graphics_mcp.backends.pillow import PillowBackend
from graphics_mcp.config import get_logger_instance
from graphics_mcp.models import (
    CropOptions,
    FilterOptions,
    FilterType,
    ResizeMode,
    ResizeOptions,
    ToolResponse,
)

logger = get_logger_instance("graphics-mcp.tools.raster")


def register_raster_tools(app: Any, backend: PillowBackend) -> None:
    """Register raster graphics tools with the MCP server."""

    @app.tool()
    async def resize_image(
        image_path: str,
        width: int | None = None,
        height: int | None = None,
        mode: str = "fit",
        maintain_aspect: bool = True,
        upscale: bool = False,
        output_path: str | None = None,
    ) -> ToolResponse:
        """Resize an image to specified dimensions.

        Args:
            image_path: Path to the source image
            width: Target width in pixels (optional if height provided)
            height: Target height in pixels (optional if width provided)
            mode: Resize mode - fit, fill, exact, or crop (default: fit)
            maintain_aspect: Maintain aspect ratio (default: true)
            upscale: Allow upscaling smaller images (default: false)
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path and dimension details
        """
        logger.info(
            "Resizing image",
            path=image_path,
            width=width,
            height=height,
            mode=mode,
        )

        if not width and not height:
            return ToolResponse(
                success=False,
                message="Either width or height must be specified",
                error="No dimensions provided",
            )

        try:
            # Validate mode
            try:
                resize_mode = ResizeMode(mode.lower())
            except ValueError:
                valid = [m.value for m in ResizeMode]
                return ToolResponse(
                    success=False,
                    message=f"Invalid mode: {mode}",
                    error=f"Valid modes: {valid}",
                )

            options = ResizeOptions(
                width=width,
                height=height,
                mode=resize_mode,
                maintain_aspect=maintain_aspect,
                upscale=upscale,
            )

            result = await backend.resize(image_path, options, output_path)

            if result.success:
                return ToolResponse(
                    success=True,
                    message=result.message,
                    data={
                        "output_path": result.output_path,
                        "original_size": result.original_size,
                        "new_size": result.new_size,
                    },
                    next_steps=[
                        "Apply filters with apply_filter tool",
                        "Convert format with convert_image tool",
                    ],
                )
            else:
                return ToolResponse(
                    success=False,
                    message=result.message,
                    error=result.error,
                )

        except Exception as e:
            logger.error("Resize failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Image resize failed",
                error=str(e),
            )

    @app.tool()
    async def crop_image(
        image_path: str,
        left: int,
        top: int,
        right: int,
        bottom: int,
        output_path: str | None = None,
    ) -> ToolResponse:
        """Crop an image to specified boundaries.

        Args:
            image_path: Path to the source image
            left: Left boundary in pixels
            top: Top boundary in pixels
            right: Right boundary in pixels
            bottom: Bottom boundary in pixels
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path and new dimensions
        """
        logger.info(
            "Cropping image",
            path=image_path,
            box=(left, top, right, bottom),
        )

        try:
            options = CropOptions(
                left=left,
                top=top,
                right=right,
                bottom=bottom,
            )

            result = await backend.crop(image_path, options, output_path)

            if result.success:
                return ToolResponse(
                    success=True,
                    message=result.message,
                    data={
                        "output_path": result.output_path,
                        "original_size": result.original_size,
                        "new_size": result.new_size,
                    },
                )
            else:
                return ToolResponse(
                    success=False,
                    message=result.message,
                    error=result.error,
                )

        except Exception as e:
            logger.error("Crop failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Image crop failed",
                error=str(e),
            )

    @app.tool()
    async def apply_filter(
        image_path: str,
        filter_type: str,
        intensity: float = 1.0,
        output_path: str | None = None,
    ) -> ToolResponse:
        """Apply a filter effect to an image.

        Args:
            image_path: Path to the source image
            filter_type: Filter to apply (blur, sharpen, grayscale, sepia, etc.)
            intensity: Filter intensity 0.0-2.0 (default: 1.0)
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path
        """
        logger.info(
            "Applying filter",
            path=image_path,
            filter=filter_type,
            intensity=intensity,
        )

        try:
            # Validate filter type
            try:
                ft = FilterType(filter_type.lower())
            except ValueError:
                valid = [f.value for f in FilterType]
                return ToolResponse(
                    success=False,
                    message=f"Invalid filter: {filter_type}",
                    error=f"Valid filters: {valid}",
                )

            # Validate intensity
            if not 0.0 <= intensity <= 2.0:
                return ToolResponse(
                    success=False,
                    message="Intensity must be between 0.0 and 2.0",
                    error=f"Got: {intensity}",
                )

            options = FilterOptions(
                filter_type=ft,
                intensity=intensity,
            )

            result = await backend.apply_filter(image_path, options, output_path)

            if result.success:
                return ToolResponse(
                    success=True,
                    message=result.message,
                    data={"output_path": result.output_path},
                    next_steps=[
                        "Apply additional filters",
                        "Resize or crop the result",
                    ],
                )
            else:
                return ToolResponse(
                    success=False,
                    message=result.message,
                    error=result.error,
                )

        except Exception as e:
            logger.error("Filter failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Filter application failed",
                error=str(e),
            )

    @app.tool()
    async def rotate_image(
        image_path: str,
        degrees: float,
        output_path: str | None = None,
    ) -> ToolResponse:
        """Rotate an image by specified degrees.

        Args:
            image_path: Path to the source image
            degrees: Rotation angle in degrees (clockwise)
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path and new dimensions
        """
        logger.info("Rotating image", path=image_path, degrees=degrees)

        try:
            result = await backend.rotate(image_path, degrees, output_path)

            if result.success:
                return ToolResponse(
                    success=True,
                    message=result.message,
                    data={
                        "output_path": result.output_path,
                        "original_size": result.original_size,
                        "new_size": result.new_size,
                    },
                )
            else:
                return ToolResponse(
                    success=False,
                    message=result.message,
                    error=result.error,
                )

        except Exception as e:
            logger.error("Rotation failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Image rotation failed",
                error=str(e),
            )

    @app.tool()
    async def flip_image(
        image_path: str,
        direction: str = "vertical",
        output_path: str | None = None,
    ) -> ToolResponse:
        """Flip an image horizontally or vertically.

        Args:
            image_path: Path to the source image
            direction: Flip direction - "horizontal" or "vertical" (default: vertical)
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path
        """
        logger.info("Flipping image", path=image_path, direction=direction)

        try:
            horizontal = direction.lower() == "horizontal"
            result = await backend.flip(image_path, horizontal, output_path)

            if result.success:
                return ToolResponse(
                    success=True,
                    message=result.message,
                    data={"output_path": result.output_path},
                )
            else:
                return ToolResponse(
                    success=False,
                    message=result.message,
                    error=result.error,
                )

        except Exception as e:
            logger.error("Flip failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Image flip failed",
                error=str(e),
            )

    @app.tool()
    async def create_thumbnail(
        image_path: str,
        width: int,
        height: int,
        output_path: str | None = None,
    ) -> ToolResponse:
        """Create a thumbnail from an image.

        Args:
            image_path: Path to the source image
            width: Maximum thumbnail width
            height: Maximum thumbnail height
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path and thumbnail dimensions
        """
        logger.info(
            "Creating thumbnail",
            path=image_path,
            size=(width, height),
        )

        try:
            result = await backend.thumbnail(image_path, (width, height), output_path)

            if result.success:
                return ToolResponse(
                    success=True,
                    message=result.message,
                    data={
                        "output_path": result.output_path,
                        "original_size": result.original_size,
                        "thumbnail_size": result.new_size,
                    },
                )
            else:
                return ToolResponse(
                    success=False,
                    message=result.message,
                    error=result.error,
                )

        except Exception as e:
            logger.error("Thumbnail creation failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Thumbnail creation failed",
                error=str(e),
            )

    @app.tool()
    async def list_available_filters() -> ToolResponse:
        """List all available image filters.

        Returns:
            ToolResponse with filter names and descriptions
        """
        filters = {
            "blur": "Apply Gaussian blur effect",
            "sharpen": "Sharpen image edges",
            "edge_enhance": "Enhance edge detection",
            "emboss": "Create embossed relief effect",
            "smooth": "Smooth image noise",
            "grayscale": "Convert to grayscale",
            "sepia": "Apply sepia tone effect",
            "invert": "Invert colors",
            "contrast": "Adjust contrast (use intensity)",
            "brightness": "Adjust brightness (use intensity)",
        }

        return ToolResponse(
            success=True,
            message="Available filters retrieved",
            data={
                "filters": filters,
                "intensity_range": "0.0 - 2.0 (1.0 = normal)",
            },
        )
