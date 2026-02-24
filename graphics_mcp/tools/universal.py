"""Universal graphics tools for MCP server."""

from __future__ import annotations

from typing import Any

from graphics_mcp.backends.pillow import PillowBackend
from graphics_mcp.config import get_logger_instance, get_settings
from graphics_mcp.models import (
    ConvertOptions,
    ImageFormat,
    ImageInfo,
    ToolResponse,
)

logger = get_logger_instance("graphics-mcp.tools.universal")


def register_universal_tools(app: Any, backend: PillowBackend) -> None:
    """Register universal graphics tools with the MCP server."""

    @app.tool()
    async def get_image_info(image_path: str) -> ToolResponse:
        """Get detailed information about an image file.

        Args:
            image_path: Path to the image file

        Returns:
            ImageInfo with dimensions, format, mode, and file size
        """
        logger.info("Getting image info", path=image_path)

        try:
            info = await backend.get_info(image_path)

            return ToolResponse(
                success=True,
                message=f"Image info retrieved for {image_path}",
                data=info.model_dump(),
            )

        except FileNotFoundError as e:
            return ToolResponse(
                success=False,
                message="Image file not found",
                error=str(e),
            )
        except ValueError as e:
            return ToolResponse(
                success=False,
                message="Invalid path or file",
                error=str(e),
            )
        except Exception as e:
            logger.error("Failed to get image info", error=str(e))
            return ToolResponse(
                success=False,
                message="Failed to get image info",
                error=str(e),
            )

    @app.tool()
    async def convert_image(
        image_path: str,
        output_format: str,
        quality: int = 85,
        optimize: bool = True,
        output_path: str | None = None,
    ) -> ToolResponse:
        """Convert an image to a different format.

        Args:
            image_path: Path to the source image
            output_format: Target format (JPEG, PNG, GIF, BMP, WEBP, TIFF)
            quality: Quality for lossy formats (1-100, default 85)
            optimize: Whether to optimize output file size
            output_path: Optional custom output path

        Returns:
            ToolResponse with output path and conversion details
        """
        logger.info(
            "Converting image",
            path=image_path,
            format=output_format,
        )

        try:
            # Validate format
            try:
                target_format = ImageFormat(output_format.upper())
            except ValueError:
                valid = [f.value for f in ImageFormat]
                return ToolResponse(
                    success=False,
                    message=f"Invalid format: {output_format}",
                    error=f"Valid formats: {valid}",
                )

            options = ConvertOptions(
                output_format=target_format,
                quality=quality,
                optimize=optimize,
            )

            result = await backend.convert(image_path, options, output_path)

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
            logger.error("Conversion failed", error=str(e))
            return ToolResponse(
                success=False,
                message="Image conversion failed",
                error=str(e),
            )

    @app.tool()
    async def list_allowed_directories() -> ToolResponse:
        """List directories where file operations are allowed.

        Returns:
            ToolResponse with list of allowed directory paths
        """
        settings = get_settings()

        return ToolResponse(
            success=True,
            message="Allowed directories retrieved",
            data={
                "directories": settings.allowed_directories,
                "max_file_size_mb": settings.max_file_size_mb,
                "allowed_formats": settings.allowed_formats,
            },
        )

    @app.tool()
    async def list_supported_formats() -> ToolResponse:
        """List all supported image formats.

        Returns:
            ToolResponse with list of supported formats and their capabilities
        """
        formats = {
            "JPEG": {
                "extension": ".jpg, .jpeg",
                "supports_transparency": False,
                "lossy": True,
            },
            "PNG": {
                "extension": ".png",
                "supports_transparency": True,
                "lossy": False,
            },
            "GIF": {
                "extension": ".gif",
                "supports_transparency": True,
                "lossy": False,
                "animation": True,
            },
            "BMP": {
                "extension": ".bmp",
                "supports_transparency": False,
                "lossy": False,
            },
            "WEBP": {
                "extension": ".webp",
                "supports_transparency": True,
                "lossy": True,
            },
            "TIFF": {
                "extension": ".tiff, .tif",
                "supports_transparency": True,
                "lossy": False,
            },
        }

        return ToolResponse(
            success=True,
            message="Supported formats retrieved",
            data={"formats": formats},
        )
