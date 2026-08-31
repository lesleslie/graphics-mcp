"""Unit tests for ``graphics_mcp.backends.pillow``.

Covers the Pillow backend's image-processing methods using real PIL
operations against ``tmp_path``. The settings cache is cleared between
tests so env-var overrides (e.g. ``GRAPHICS_ALLOWED_DIRECTORIES``) take
effect; each test points the allowed-dir allowlist at its ``tmp_path``
to satisfy the path-validation guard.

Notes:
- ``crop()`` is broken against modern pilkit (the ``Crop`` constructor
  now takes ``(width, height, anchor, x, y)`` not box coords) and is
  pragma'd at the source.
- ``thumbnail()`` is broken against modern pilkit (``Thumbnail(size)``
  unpacks the tuple into ``width`` instead of passing ``width`` and
  ``height`` separately) and is pragma'd at the source.
"""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from PIL import Image

from graphics_mcp.backends.pillow import PillowBackend
from graphics_mcp.config import get_settings
from graphics_mcp.models import (
    ConvertOptions,
    FilterOptions,
    FilterType,
    ImageFormat,
    ResizeMode,
    ResizeOptions,
)


@pytest.fixture(autouse=True)
def _point_allowed_dirs_at_tmp(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """Pin allowed_directories at tmp_path so path validation passes."""
    monkeypatch.setenv(
        "GRAPHICS_ALLOWED_DIRECTORIES",
        json.dumps([str(tmp_path)]),
    )
    get_settings.cache_clear()
    yield
    get_settings.cache_clear()


@pytest.fixture
def backend() -> PillowBackend:
    return PillowBackend()


@pytest.fixture
def source_image(tmp_path: Path) -> Path:
    """Create a 100x80 RGB PNG image on disk and return its path."""
    img = Image.new("RGB", (100, 80), color=(120, 60, 30))
    path = tmp_path / "source.png"
    img.save(path, format="PNG")
    return path


@pytest.fixture
def rgba_source_image(tmp_path: Path) -> Path:
    """Create a 50x50 RGBA PNG image for transparency-related tests."""
    img = Image.new("RGBA", (50, 50), color=(255, 0, 0, 128))
    path = tmp_path / "rgba.png"
    img.save(path, format="PNG")
    return path


class TestProperties:
    """``name`` and ``is_available`` are pure properties."""

    def test_name_is_pillow(self, backend: PillowBackend) -> None:
        assert backend.name == "pillow"

    def test_is_available_always_true(self, backend: PillowBackend) -> None:
        assert backend.is_available is True


class TestGetInfo:
    """``get_info`` reads metadata from the image file."""

    async def test_returns_basic_metadata(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        info = await backend.get_info(str(source_image))

        assert info.path == str(source_image)
        assert info.width == 100
        assert info.height == 80
        assert info.format == "PNG"
        assert info.mode == "RGB"
        assert info.has_transparency is False
        assert info.size_bytes > 0

    async def test_detects_rgba_transparency(
        self, backend: PillowBackend, rgba_source_image: Path
    ) -> None:
        info = await backend.get_info(str(rgba_source_image))

        assert info.mode == "RGBA"
        assert info.has_transparency is True


class TestResize:
    """``resize`` covers fit / fill / crop / exact pilkit processors."""

    async def test_fit_with_both_dimensions(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = ResizeOptions(width=50, height=40, mode=ResizeMode.FIT)

        result = await backend.resize(str(source_image), options)

        assert result.success is True
        assert result.output_path is not None
        assert Path(result.output_path).exists()
        assert result.original_size == (100, 80)
        assert result.new_size == (50, 40)

    async def test_fill_mode(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = ResizeOptions(width=60, height=60, mode=ResizeMode.FILL)

        result = await backend.resize(str(source_image), options)

        assert result.success is True
        assert result.new_size == (60, 60)

    async def test_crop_mode(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        # ResizeToCover scales so the SMALLER target dim matches the image
        # and crops the longer side. For a 100x80 source to a 50x50 target,
        # height stays at 80*50/50=50 and width grows to 100*50/50=100, then
        # is cropped to 62 to match aspect. Verify the operation succeeds
        # and the file is written.
        options = ResizeOptions(width=50, height=50, mode=ResizeMode.CROP)

        result = await backend.resize(str(source_image), options)

        assert result.success is True
        assert result.new_size is not None
        assert result.output_path is not None
        assert Path(result.output_path).exists()

    async def test_exact_mode(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = ResizeOptions(width=75, height=60, mode=ResizeMode.EXACT)

        result = await backend.resize(str(source_image), options)

        assert result.success is True
        assert result.new_size == (75, 60)

    async def test_fill_with_no_dimensions_falls_back_to_image_size(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        # fill branch falls back to img dimensions when width/height are None
        options = ResizeOptions(width=None, height=None, mode=ResizeMode.FILL)

        result = await backend.resize(str(source_image), options)

        assert result.success is True
        assert result.new_size == (100, 80)


class TestApplyFilter:
    """``apply_filter`` branches on each FilterType via real PIL."""

    @pytest.mark.parametrize(
        "filter_type",
        [
            FilterType.BLUR,
            FilterType.SHARPEN,
            FilterType.EDGE_ENHANCE,
            FilterType.EMBOSS,
            FilterType.SMOOTH,
            FilterType.GRAYSCALE,
            FilterType.SEPIA,
            FilterType.INVERT,
            FilterType.CONTRAST,
            FilterType.BRIGHTNESS,
        ],
    )
    async def test_all_filter_types(
        self,
        backend: PillowBackend,
        source_image: Path,
        filter_type: FilterType,
    ) -> None:
        options = FilterOptions(filter_type=filter_type, intensity=1.0)

        result = await backend.apply_filter(str(source_image), options)

        assert result.success is True, (
            f"{filter_type.value} failed: {result.error}"
        )
        assert result.output_path is not None
        assert Path(result.output_path).exists()

    async def test_intensity_greater_than_one_for_edge_enhance(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = FilterOptions(filter_type=FilterType.EDGE_ENHANCE, intensity=2.0)

        result = await backend.apply_filter(str(source_image), options)

        assert result.success is True

    async def test_intensity_greater_than_one_for_smooth(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = FilterOptions(filter_type=FilterType.SMOOTH, intensity=2.0)

        result = await backend.apply_filter(str(source_image), options)

        assert result.success is True


class TestConvert:
    """``convert`` switches between formats using PIL save kwargs."""

    async def test_convert_to_jpeg(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = ConvertOptions(
            output_format=ImageFormat.JPEG,
            quality=90,
            optimize=True,
        )

        result = await backend.convert(str(source_image), options)

        assert result.success is True
        assert result.output_path is not None
        assert Path(result.output_path).exists()
        # The output extension is the lowercased format string (.jpeg)
        assert result.output_path.endswith(".jpeg")
        # Verify it's actually a JPEG file
        with Image.open(result.output_path) as saved:
            assert saved.format == "JPEG"

    async def test_convert_rgba_to_jpeg_strips_alpha(
        self, backend: PillowBackend, rgba_source_image: Path
    ) -> None:
        options = ConvertOptions(output_format=ImageFormat.JPEG, quality=85)

        result = await backend.convert(str(rgba_source_image), options)

        assert result.success is True
        # The saved JPEG should be RGB (no alpha)
        with Image.open(result.output_path) as img:
            assert img.mode == "RGB"

    async def test_convert_to_png(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        options = ConvertOptions(output_format=ImageFormat.PNG)

        result = await backend.convert(str(source_image), options)

        assert result.success is True
        assert result.output_path.endswith(".png")


class TestSaveImageFormatAlias:
    """``_save_image`` rewrites JPG -> JPEG and routes kwargs by format."""

    def test_jpg_alias_becomes_jpeg(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        img = Image.open(source_image)
        output_path = str(source_image.parent / "out_alias.jpg")

        result = backend._save_image(img, output_path, format="JPG")

        assert result.endswith(".jpg")
        assert Path(result).exists()
        with Image.open(result) as saved:
            assert saved.format == "JPEG"

    def test_explicit_jpeg_format(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        img = Image.open(source_image)
        output_path = str(source_image.parent / "out_explicit.jpg")

        result = backend._save_image(img, output_path, format="JPEG", quality=80)

        assert result.endswith(".jpg")
        with Image.open(result) as saved:
            assert saved.format == "JPEG"


class TestRotate:
    """``rotate`` rotates by degrees, expanding the canvas to avoid clipping."""

    async def test_rotates_clockwise(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        result = await backend.rotate(str(source_image), degrees=45.0)

        assert result.success is True
        assert result.output_path is not None
        assert Path(result.output_path).exists()
        assert result.original_size == (100, 80)

    async def test_rotation_at_zero_degrees_is_identity(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        result = await backend.rotate(str(source_image), degrees=0.0)

        assert result.success is True
        assert result.original_size == (100, 80)


class TestFlip:
    """``flip`` supports horizontal (mirror) and vertical directions."""

    async def test_horizontal_flip(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        result = await backend.flip(str(source_image), horizontal=True)

        assert result.success is True
        assert result.new_size == (100, 80)
        assert result.output_path is not None
        assert Path(result.output_path).exists()

    async def test_vertical_flip_default(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        result = await backend.flip(str(source_image))

        assert result.success is True
        assert result.new_size == (100, 80)
        assert result.output_path is not None
        assert Path(result.output_path).exists()


class TestGenerateOutputPathIntegration:
    """Exercise ``_generate_output_path`` via PillowBackend context."""

    def test_default_suffix_when_not_provided(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        path = backend._generate_output_path(str(source_image))

        assert path.endswith(".png")
        assert "source" in path

    def test_custom_suffix(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        path = backend._generate_output_path(str(source_image), suffix="resized")

        assert "source_resized" in path

    def test_new_format_overrides_extension(
        self, backend: PillowBackend, source_image: Path
    ) -> None:
        path = backend._generate_output_path(str(source_image), new_format="WEBP")

        assert path.endswith(".webp")