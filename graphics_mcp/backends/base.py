"""Abstract base class for graphics backends."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from graphics_mcp.models import (
        ConvertOptions,
        CropOptions,
        FilterOptions,
        ImageInfo,
        ResizeOptions,
        TransformResult,
)


class GraphicsBackend(Protocol):
    """Protocol defining the interface for graphics backends."""

    @property
    def name(self) -> str:
        """Backend name identifier."""
        ...

    @property
    def is_available(self) -> bool:
        """Check if backend is available on this system."""
        ...

    async def get_info(self, image_path: str) -> ImageInfo:
        """Get image metadata."""
        ...

    async def resize(
        self,
        image_path: str,
        options: ResizeOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Resize an image."""
        ...

    async def crop(
        self,
        image_path: str,
        options: CropOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Crop an image."""
        ...

    async def apply_filter(
        self,
        image_path: str,
        options: FilterOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Apply a filter to an image."""
        ...

    async def convert(
        self,
        image_path: str,
        options: ConvertOptions,
        output_path: str | None = None,
    ) -> TransformResult:
        """Convert image format."""
        ...

    async def rotate(
        self,
        image_path: str,
        degrees: float,
        output_path: str | None = None,
    ) -> TransformResult:
        """Rotate an image."""
        ...

    async def flip(
        self,
        image_path: str,
        horizontal: bool = False,
        output_path: str | None = None,
    ) -> TransformResult:
        """Flip an image horizontally or vertically."""
        ...


class BaseGraphicsBackend(ABC):
    """Abstract base class providing common functionality for backends."""

    def __init__(self, config: dict[str, Any] | None = None) -> None:
        self.config = config or {}

    @property
    @abstractmethod
    def name(self) -> str:
        """Backend name identifier."""
        ...

    @property
    @abstractmethod
    def is_available(self) -> bool:
        """Check if backend is available on this system."""
        ...

    def _validate_path(self, path: str, allowed_dirs: list[str]) -> Path:
        """Validate that path is within allowed directories."""
        from graphics_mcp.config import get_settings

        settings = get_settings()
        expanded = Path(path).expanduser().resolve()

        # Check allowed directories
        for allowed in allowed_dirs:
            allowed_path = Path(allowed).expanduser().resolve()
            try:
                expanded.relative_to(allowed_path)
                return expanded
            except ValueError:
                continue

        raise ValueError(
            f"Path '{path}' is not within allowed directories: {allowed_dirs}"
        )

    def _generate_output_path(
        self,
        source_path: str,
        suffix: str = "",
        new_format: str | None = None,
    ) -> str:
        """Generate output path for transformed image."""
        source = Path(source_path)
        stem = source.stem

        if suffix:
            stem = f"{stem}_{suffix}"

        if new_format:
            ext = f".{new_format.lower()}"
        else:
            ext = source.suffix

        return str(source.parent / f"{stem}{ext}")

    def _check_file_size(self, path: str, max_mb: int) -> None:
        """Check that file size is within limits."""
        file_path = Path(path)
        if not file_path.exists():
            raise FileNotFoundError(f"Image not found: {path}")

        size_mb = file_path.stat().st_size / (1024 * 1024)
        if size_mb > max_mb:
            raise ValueError(
                f"File size ({size_mb:.1f}MB) exceeds maximum ({max_mb}MB)"
            )
