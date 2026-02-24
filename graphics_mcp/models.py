"""Pydantic models for graphics operations."""

from __future__ import annotations

from enum import Enum
from pathlib import Path
from typing import Annotated, Any

from pydantic import BaseModel, Field, field_validator


class ImageFormat(str, Enum):
    """Supported image formats."""

    JPEG = "JPEG"
    PNG = "PNG"
    GIF = "GIF"
    BMP = "BMP"
    WEBP = "WEBP"
    TIFF = "TIFF"
    ICO = "ICO"


class ResizeMode(str, Enum):
    """Resize mode options."""

    FIT = "fit"  # Fit within dimensions, maintain aspect ratio
    FILL = "fill"  # Fill dimensions, may crop
    EXACT = "exact"  # Exact dimensions, may distort
    CROP = "crop"  # Crop to exact dimensions


class FilterType(str, Enum):
    """Available image filters."""

    BLUR = "blur"
    SHARPEN = "sharpen"
    EDGE_ENHANCE = "edge_enhance"
    EMBOSS = "emboss"
    SMOOTH = "smooth"
    GRAYSCALE = "grayscale"
    SEPIA = "sepia"
    INVERT = "invert"
    CONTRAST = "contrast"
    BRIGHTNESS = "brightness"


class ImageInfo(BaseModel):
    """Image metadata information."""

    path: str = Field(description="Path to the image file")
    width: int = Field(description="Image width in pixels")
    height: int = Field(description="Image height in pixels")
    format: str = Field(description="Image format (JPEG, PNG, etc.)")
    mode: str = Field(description="Color mode (RGB, RGBA, L, etc.)")
    size_bytes: int = Field(description="File size in bytes")
    has_transparency: bool = Field(description="Whether image has alpha channel")


class ResizeOptions(BaseModel):
    """Options for resize operations."""

    width: int | None = Field(default=None, ge=1, description="Target width")
    height: int | None = Field(default=None, ge=1, description="Target height")
    mode: ResizeMode = Field(default=ResizeMode.FIT, description="Resize mode")
    maintain_aspect: bool = Field(default=True, description="Maintain aspect ratio")
    upscale: bool = Field(default=False, description="Allow upscaling")

    @field_validator("width", "height")
    @classmethod
    def validate_dimensions(cls, v: int | None) -> int | None:
        if v is not None and v < 1:
            raise ValueError("Dimensions must be positive")
        return v


class CropOptions(BaseModel):
    """Options for crop operations."""

    left: int = Field(ge=0, description="Left crop boundary")
    top: int = Field(ge=0, description="Top crop boundary")
    right: int = Field(ge=0, description="Right crop boundary")
    bottom: int = Field(ge=0, description="Bottom crop boundary")

    @field_validator("right")
    @classmethod
    def validate_right(cls, v: int, info: Any) -> int:
        if "left" in info.data and v <= info.data["left"]:
            raise ValueError("Right must be greater than left")
        return v

    @field_validator("bottom")
    @classmethod
    def validate_bottom(cls, v: int, info: Any) -> int:
        if "top" in info.data and v <= info.data["top"]:
            raise ValueError("Bottom must be greater than top")
        return v


class FilterOptions(BaseModel):
    """Options for filter operations."""

    filter_type: FilterType = Field(description="Type of filter to apply")
    intensity: float = Field(
        default=1.0,
        ge=0.0,
        le=2.0,
        description="Filter intensity (0.0-2.0)",
    )


class ConvertOptions(BaseModel):
    """Options for format conversion."""

    output_format: ImageFormat = Field(description="Target output format")
    quality: int = Field(
        default=85,
        ge=1,
        le=100,
        description="Quality for lossy formats (1-100)",
    )
    optimize: bool = Field(default=True, description="Optimize output file size")


class TransformResult(BaseModel):
    """Result of a transform operation."""

    success: bool = Field(description="Whether the operation succeeded")
    source_path: str = Field(description="Original image path")
    output_path: str | None = Field(default=None, description="Output image path")
    message: str = Field(description="Human-readable result message")
    original_size: tuple[int, int] | None = Field(
        default=None,
        description="Original dimensions (width, height)",
    )
    new_size: tuple[int, int] | None = Field(
        default=None,
        description="New dimensions (width, height)",
    )
    error: str | None = Field(default=None, description="Error message if failed")


class ToolResponse(BaseModel):
    """Standard response format for MCP tools."""

    success: bool = Field(description="Whether the operation succeeded")
    message: str = Field(description="Human-readable result message")
    data: dict[str, Any] | None = Field(default=None, description="Response data")
    error: str | None = Field(default=None, description="Error message if failed")
    next_steps: list[str] | None = Field(
        default=None,
        description="Suggested next actions",
    )


# Path type for validation
SafePath = Annotated[str, Field(pattern=r"^[a-zA-Z0-9_\-./]+$")]
