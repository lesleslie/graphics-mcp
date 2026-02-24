"""Pillow backend for graphics operations with pilkit integration."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Any

from PIL import Image, ImageEnhance, ImageFilter, ImageOps
from pilkit.processors import (
    Adjust,
    Crop,
    MakeOpaque,
    Resize,
    ResizeToCover,
    ResizeToFill,
    Thumbnail,
)

from graphics_mcp.backends.base import BaseGraphicsBackend
from graphics_mcp.config import get_logger_instance, get_settings

if TYPE_CHECKING:
    from graphics_mcp.models import (
        ConvertOptions,
        CropOptions,
        FilterOptions,
        ImageInfo,
        ResizeOptions,
        TransformResult,
    )

logger = get_logger_instance("graphics-mcp.backends.pillow")


class PillowBackend(BaseGraphicsBackend):
    """Pillow-based graphics backend with pilkit processors."""

    @property
    def name(self) -> str:
        return "pillow"

    @property
    def is_available(self) -> bool:
        """Pillow is always available if the package is installed."""
        return True

    def _open_image(self, path: str) -> Image.Image:
        """Open an image file with validation."""
        settings = get_settings()
        validated_path = self._validate_path(path, settings.allowed_directories)
        self._check_file_size(str(validated_path), settings.max_file_size_mb)

        return Image.open(validated_path)

    def _save_image(
        self,
        img: Image.Image,
        output_path: str,
        format: str | None = None,
        quality: int = 85,
        optimize: bool = True,
    ) -> str:
        """Save an image to file."""
        settings = get_settings()
        validated_path = self._validate_path(
            str(Path(output_path).parent),
            settings.allowed_directories,
        )

        output = Path(validated_path) / Path(output_path).name

        # Determine format
        save_format = format or img.format or "PNG"
        if save_format.upper() == "JPG":
            save_format = "JPEG"

        # Handle format-specific options
        save_kwargs: dict[str, Any] = {}
        if save_format.upper() in ("JPEG", "WEBP"):
            save_kwargs["quality"] = quality
            save_kwargs["optimize"] = optimize
        elif save_format.upper() == "PNG":
            save_kwargs["optimize"] = optimize

        # Convert RGBA to RGB for JPEG
        if save_format.upper() == "JPEG" and img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGB")

        img.save(output, format=save_format, **save_kwargs)
        return str(output)

    async def get_info(self, image_path: str) -> ImageInfo:
        """Get image metadata."""
        logger.debug("Getting image info", path=image_path)

        img = self._open_image(image_path)
        path = Path(image_path)

        return ImageInfo(
            path=image_path,
            width=img.width,
            height=img.height,
            format=img.format or "UNKNOWN",
            mode=img.mode,
            size_bytes=path.stat().st_size,
            has_transparency=img.mode in ("RGBA", "LA", "P"),
        )

    async def resize(
        self,
        image_path: str,
        options: ResizeOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Resize an image using pilkit processors."""
        logger.info(
            "Resizing image",
            path=image_path,
            width=options.width,
            height=options.height,
            mode=options.mode,
        )

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            # Choose appropriate pilkit processor based on mode
            if options.mode.value == "fit":
                # Fit within dimensions maintaining aspect ratio
                if options.width and options.height:
                    processor = Resize(options.width, options.height, upscale=options.upscale)
                elif options.width:
                    processor = Resize(options.width, upscale=options.upscale)
                else:
                    processor = Resize(height=options.height, upscale=options.upscale)
            elif options.mode.value == "fill":
                # Fill dimensions, may crop
                processor = ResizeToFill(options.width or img.width, options.height or img.height)
            elif options.mode.value == "crop":
                # Crop to exact dimensions
                processor = ResizeToCover(options.width or img.width, options.height or img.height)
            else:
                # Exact resize (may distort)
                processor = Resize(options.width or img.width, options.height or img.height, upscale=options.upscale)

            processed = processor.process(img)

            # Generate output path
            if not output_path:
                output_path = self._generate_output_path(image_path, "resized")

            final_path = self._save_image(processed, output_path)
            new_size = (processed.width, processed.height)

            logger.info("Resize complete", output=final_path, new_size=new_size)

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Resized from {original_size} to {new_size}",
                original_size=original_size,
                new_size=new_size,
            )

        except Exception as e:
            logger.error("Resize failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Resize operation failed",
                error=str(e),
            )

    async def crop(
        self,
        image_path: str,
        options: CropOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Crop an image using pilkit Crop processor."""
        logger.info(
            "Cropping image",
            path=image_path,
            box=(options.left, options.top, options.right, options.bottom),
        )

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            # Use pilkit Crop processor
            processor = Crop(
                options.left,
                options.top,
                options.right,
                options.bottom,
            )
            processed = processor.process(img)

            if not output_path:
                output_path = self._generate_output_path(image_path, "cropped")

            final_path = self._save_image(processed, output_path)
            new_size = (processed.width, processed.height)

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Cropped from {original_size} to {new_size}",
                original_size=original_size,
                new_size=new_size,
            )

        except Exception as e:
            logger.error("Crop failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Crop operation failed",
                error=str(e),
            )

    async def apply_filter(
        self,
        image_path: str,
        options: FilterOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Apply a filter to an image."""
        logger.info(
            "Applying filter",
            path=image_path,
            filter=options.filter_type.value,
            intensity=options.intensity,
        )

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            # Apply filter based on type
            filter_type = options.filter_type.value
            intensity = options.intensity

            if filter_type == "blur":
                img = img.filter(ImageFilter.GaussianBlur(radius=intensity * 2))
            elif filter_type == "sharpen":
                img = img.filter(ImageFilter.UnsharpMask(radius=intensity))
            elif filter_type == "edge_enhance":
                img = img.filter(ImageFilter.EDGE_ENHANCE_MORE if intensity > 1 else ImageFilter.EDGE_ENHANCE)
            elif filter_type == "emboss":
                img = img.filter(ImageFilter.EMBOSS)
            elif filter_type == "smooth":
                img = img.filter(ImageFilter.SMOOTH_MORE if intensity > 1 else ImageFilter.SMOOTH)
            elif filter_type == "grayscale":
                img = ImageOps.grayscale(img)
                if img.mode == "L":
                    img = img.convert("RGB")
            elif filter_type == "sepia":
                img = ImageOps.sepia(img)
            elif filter_type == "invert":
                img = ImageOps.invert(img.convert("RGB"))
            elif filter_type == "contrast":
                enhancer = ImageEnhance.Contrast(img)
                img = enhancer.enhance(intensity)
            elif filter_type == "brightness":
                enhancer = ImageEnhance.Brightness(img)
                img = enhancer.enhance(intensity)
            else:
                raise ValueError(f"Unknown filter: {filter_type}")

            if not output_path:
                output_path = self._generate_output_path(image_path, filter_type)

            final_path = self._save_image(img, output_path)

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Applied {filter_type} filter",
                original_size=original_size,
                new_size=original_size,  # Filters don't change dimensions
            )

        except Exception as e:
            logger.error("Filter failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Filter operation failed",
                error=str(e),
            )

    async def convert(
        self,
        image_path: str,
        options: ConvertOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Convert image format."""
        logger.info(
            "Converting image",
            path=image_path,
            target_format=options.output_format.value,
            quality=options.quality,
        )

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            target_format = options.output_format.value

            if not output_path:
                output_path = self._generate_output_path(
                    image_path,
                    new_format=target_format,
                )

            final_path = self._save_image(
                img,
                output_path,
                format=target_format,
                quality=options.quality,
                optimize=options.optimize,
            )

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Converted to {target_format}",
                original_size=original_size,
                new_size=original_size,
            )

        except Exception as e:
            logger.error("Conversion failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Conversion operation failed",
                error=str(e),
            )

    async def rotate(
        self,
        image_path: str,
        degrees: float,
        output_path: str | None = None,
    ) -> TransformResult:
        """Rotate an image."""
        logger.info("Rotating image", path=image_path, degrees=degrees)

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            # Rotate with expand=True to avoid clipping
            rotated = img.rotate(-degrees, expand=True)  # Negative for clockwise
            new_size = (rotated.width, rotated.height)

            if not output_path:
                output_path = self._generate_output_path(image_path, f"rotated_{int(degrees)}")

            final_path = self._save_image(rotated, output_path)

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Rotated {degrees} degrees",
                original_size=original_size,
                new_size=new_size,
            )

        except Exception as e:
            logger.error("Rotation failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Rotation operation failed",
                error=str(e),
            )

    async def flip(
        self,
        image_path: str,
        horizontal: bool = False,
        output_path: str | None = None,
    ) -> TransformResult:
        """Flip an image horizontally or vertically."""
        direction = "horizontal" if horizontal else "vertical"
        logger.info("Flipping image", path=image_path, direction=direction)

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            if horizontal:
                flipped = ImageOps.mirror(img)
            else:
                flipped = ImageOps.flip(img)

            if not output_path:
                output_path = self._generate_output_path(image_path, f"flipped_{direction}")

            final_path = self._save_image(flipped, output_path)

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Flipped {direction}",
                original_size=original_size,
                new_size=original_size,
            )

        except Exception as e:
            logger.error("Flip failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Flip operation failed",
                error=str(e),
            )

    async def thumbnail(
        self,
        image_path: str,
        size: tuple[int, int],
        output_path: str | None = None,
    ) -> TransformResult:
        """Create a thumbnail using pilkit Thumbnail processor."""
        logger.info("Creating thumbnail", path=image_path, size=size)

        try:
            img = self._open_image(image_path)
            original_size = (img.width, img.height)

            processor = Thumbnail(size)
            processed = processor.process(img)
            new_size = (processed.width, processed.height)

            if not output_path:
                output_path = self._generate_output_path(image_path, "thumb")

            final_path = self._save_image(processed, output_path)

            return TransformResult(
                success=True,
                source_path=image_path,
                output_path=final_path,
                message=f"Created thumbnail {new_size}",
                original_size=original_size,
                new_size=new_size,
            )

        except Exception as e:
            logger.error("Thumbnail failed", error=str(e))
            return TransformResult(
                success=False,
                source_path=image_path,
                message="Thumbnail operation failed",
                error=str(e),
            )
