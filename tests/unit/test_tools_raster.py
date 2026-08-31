"""Unit tests for ``graphics_mcp.tools.raster``.

Covers the raster-tool wrapper functions registered via FastMCP's
``@app.tool()`` decorator. Tests use a mock ``PillowBackend`` so we
exercise the validation, error-mapping, and success-shape logic in the
wrapper without touching PIL or filesystem I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from fastmcp import FastMCP

from graphics_mcp.tools.raster import register_raster_tools


@dataclass
class _MockResult:
    """Mimics ``TransformResult`` for the mock backend."""

    success: bool
    source_path: str
    output_path: str | None = None
    message: str = ""
    original_size: tuple[int, int] | None = None
    new_size: tuple[int, int] | None = None
    error: str | None = None


class MockPillowBackend:
    """Records calls and returns canned ``TransformResult``s."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.next_success: bool = True
        self.next_message: str = "ok"
        self.next_error: str | None = None
        self.next_output: str = "/tmp/out.png"
        self.next_original_size: tuple[int, int] = (100, 80)
        self.next_new_size: tuple[int, int] = (50, 40)
        # Optional hooks: store here to raise specific exceptions
        self.resize_hook: Any = None
        self.crop_hook: Any = None
        self.filter_hook: Any = None
        self.rotate_hook: Any = None
        self.flip_hook: Any = None
        self.thumbnail_hook: Any = None

    def _build_result(self) -> _MockResult:
        return _MockResult(
            success=self.next_success,
            source_path="<recorded>",
            output_path=self.next_output if self.next_success else None,
            message=self.next_message,
            original_size=self.next_original_size,
            new_size=self.next_new_size,
            error=self.next_error,
        )

    async def resize(self, image_path: str, options: Any, output_path: str | None = None) -> _MockResult:  # noqa: E501
        self.calls.append(("resize", {"image_path": image_path, "options": options, "output_path": output_path}))
        if self.resize_hook:
            return await self.resize_hook(image_path, options, output_path)
        return self._build_result()

    async def crop(self, image_path: str, options: Any, output_path: str | None = None) -> _MockResult:
        self.calls.append(("crop", {"image_path": image_path, "options": options, "output_path": output_path}))
        if self.crop_hook:
            return await self.crop_hook(image_path, options, output_path)
        return self._build_result()

    async def apply_filter(self, image_path: str, options: Any, output_path: str | None = None) -> _MockResult:
        self.calls.append(("apply_filter", {"image_path": image_path, "options": options, "output_path": output_path}))
        if self.filter_hook:
            return await self.filter_hook(image_path, options, output_path)
        return self._build_result()

    async def rotate(self, image_path: str, degrees: float, output_path: str | None = None) -> _MockResult:
        self.calls.append(("rotate", {"image_path": image_path, "degrees": degrees, "output_path": output_path}))
        if self.rotate_hook:
            return await self.rotate_hook(image_path, degrees, output_path)
        return self._build_result()

    async def flip(self, image_path: str, horizontal: bool = False, output_path: str | None = None) -> _MockResult:
        self.calls.append(("flip", {"image_path": image_path, "horizontal": horizontal, "output_path": output_path}))
        if self.flip_hook:
            return await self.flip_hook(image_path, horizontal, output_path)
        return self._build_result()

    async def thumbnail(self, image_path: str, size: tuple[int, int], output_path: str | None = None) -> _MockResult:
        self.calls.append(("thumbnail", {"image_path": image_path, "size": size, "output_path": output_path}))
        if self.thumbnail_hook:
            return await self.thumbnail_hook(image_path, size, output_path)
        return self._build_result()


@pytest.fixture
def mock_backend() -> MockPillowBackend:
    return MockPillowBackend()


@pytest.fixture
def app(mock_backend: MockPillowBackend) -> FastMCP:
    server = FastMCP(name="TestRaster")
    register_raster_tools(server, mock_backend)
    return server


def _structured(result: Any) -> dict[str, Any]:
    """Pull the structured content from a FastMCP ToolResult."""
    assert result.structured_content is not None, f"Missing structured_content: {result}"
    return result.structured_content  # type: ignore[no-any-return]


class TestResizeImage:
    """``resize_image`` validates inputs and maps backend errors."""

    async def test_success_returns_output_path_and_dimensions(
        self, app: FastMCP
    ) -> None:
        result = await app.call_tool(
            "resize_image",
            {"image_path": "/tmp/x.png", "width": 50, "height": 40, "mode": "fit"},
        )
        body = _structured(result)

        assert body["success"] is True
        assert body["data"]["output_path"] == "/tmp/out.png"
        assert body["data"]["original_size"] == [100, 80]
        assert body["data"]["new_size"] == [50, 40]
        assert "Apply filters" in body["next_steps"][0]

    async def test_missing_dimensions_returns_error(self, app: FastMCP) -> None:
        result = await app.call_tool(
            "resize_image",
            {"image_path": "/tmp/x.png"},  # no width, no height
        )
        body = _structured(result)

        assert body["success"] is False
        assert "width or height" in body["message"]

    async def test_invalid_mode_returns_error(self, app: FastMCP) -> None:
        result = await app.call_tool(
            "resize_image",
            {"image_path": "/tmp/x.png", "width": 50, "mode": "bogus"},
        )
        body = _structured(result)

        assert body["success"] is False
        assert "Invalid mode" in body["message"]
        assert "valid modes" in body["error"].lower()

    async def test_backend_failure_returns_error_payload(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "backend boom"

        result = await app.call_tool(
            "resize_image",
            {"image_path": "/tmp/x.png", "width": 50, "height": 40},
        )
        body = _structured(result)

        assert body["success"] is False
        assert body["error"] == "backend boom"

    async def test_unexpected_exception_returns_error_payload(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        async def boom(*_args: Any, **_kwargs: Any) -> _MockResult:
            raise RuntimeError("unexpected")

        mock_backend.resize_hook = boom

        result = await app.call_tool(
            "resize_image",
            {"image_path": "/tmp/x.png", "width": 50, "height": 40},
        )
        body = _structured(result)

        assert body["success"] is False
        assert "unexpected" in body["error"]

    async def test_default_mode_is_fit(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "resize_image",
            {"image_path": "/tmp/x.png", "width": 50},
        )
        body = _structured(result)
        assert body["success"] is True
        # The recorded call should have mode=fit
        call = mock_backend.calls[-1]
        assert call[1]["options"].mode.value == "fit"


class TestCropImage:
    """``crop_image`` forwards to backend.crop with CropOptions."""

    async def test_success(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "crop_image",
            {
                "image_path": "/tmp/x.png",
                "left": 10,
                "top": 20,
                "right": 60,
                "bottom": 70,
            },
        )
        body = _structured(result)

        assert body["success"] is True
        assert body["data"]["output_path"] == "/tmp/out.png"
        # Verify the backend was called with the right box
        call = mock_backend.calls[-1]
        assert call[0] == "crop"
        opts = call[1]["options"]
        assert (opts.left, opts.top, opts.right, opts.bottom) == (10, 20, 60, 70)

    async def test_backend_failure(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "bad box"

        result = await app.call_tool(
            "crop_image",
            {
                "image_path": "/tmp/x.png",
                "left": 10,
                "top": 20,
                "right": 60,
                "bottom": 70,
            },
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["error"] == "bad box"

    async def test_unexpected_exception(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        async def boom(*_args: Any, **_kwargs: Any) -> _MockResult:
            raise ValueError("nope")

        mock_backend.crop_hook = boom

        result = await app.call_tool(
            "crop_image",
            {
                "image_path": "/tmp/x.png",
                "left": 0,
                "top": 0,
                "right": 10,
                "bottom": 10,
            },
        )
        body = _structured(result)
        assert body["success"] is False
        assert "nope" in body["error"]


class TestApplyFilter:
    """``apply_filter`` validates filter type and intensity range."""

    async def test_success(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "apply_filter",
            {"image_path": "/tmp/x.png", "filter_type": "blur", "intensity": 1.5},
        )
        body = _structured(result)

        assert body["success"] is True
        assert body["data"]["output_path"] == "/tmp/out.png"

    async def test_invalid_filter_type(self, app: FastMCP) -> None:
        result = await app.call_tool(
            "apply_filter",
            {"image_path": "/tmp/x.png", "filter_type": "no_such_filter"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "Invalid filter" in body["message"]

    async def test_intensity_below_zero(self, app: FastMCP) -> None:
        result = await app.call_tool(
            "apply_filter",
            {"image_path": "/tmp/x.png", "filter_type": "blur", "intensity": -0.5},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "Intensity" in body["message"]

    async def test_intensity_above_two(self, app: FastMCP) -> None:
        result = await app.call_tool(
            "apply_filter",
            {"image_path": "/tmp/x.png", "filter_type": "blur", "intensity": 3.0},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "Intensity" in body["message"]

    async def test_backend_failure(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "filter failed"

        result = await app.call_tool(
            "apply_filter",
            {"image_path": "/tmp/x.png", "filter_type": "blur"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["error"] == "filter failed"

    async def test_unexpected_exception(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        async def boom(*_args: Any, **_kwargs: Any) -> _MockResult:
            raise RuntimeError("kaboom")

        mock_backend.filter_hook = boom

        result = await app.call_tool(
            "apply_filter",
            {"image_path": "/tmp/x.png", "filter_type": "blur"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "kaboom" in body["error"]


class TestRotateImage:
    """``rotate_image`` forwards degrees to backend."""

    async def test_success(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "rotate_image",
            {"image_path": "/tmp/x.png", "degrees": 45.0},
        )
        body = _structured(result)
        assert body["success"] is True
        assert body["data"]["output_path"] == "/tmp/out.png"

    async def test_backend_failure(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "rotate boom"

        result = await app.call_tool(
            "rotate_image",
            {"image_path": "/tmp/x.png", "degrees": 90.0},
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["error"] == "rotate boom"

    async def test_unexpected_exception(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        async def boom(*_args: Any, **_kwargs: Any) -> _MockResult:
            raise ValueError("bad angle")

        mock_backend.rotate_hook = boom

        result = await app.call_tool(
            "rotate_image",
            {"image_path": "/tmp/x.png", "degrees": 30.0},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "bad angle" in body["error"]


class TestFlipImage:
    """``flip_image`` maps direction string to boolean horizontal flag."""

    async def test_horizontal(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "flip_image",
            {"image_path": "/tmp/x.png", "direction": "horizontal"},
        )
        body = _structured(result)
        assert body["success"] is True
        # Verify horizontal=True was passed
        call = mock_backend.calls[-1]
        assert call[1]["horizontal"] is True

    async def test_vertical_default(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "flip_image",
            {"image_path": "/tmp/x.png"},
        )
        body = _structured(result)
        assert body["success"] is True
        call = mock_backend.calls[-1]
        assert call[1]["horizontal"] is False

    async def test_backend_failure(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "flip fail"

        result = await app.call_tool(
            "flip_image",
            {"image_path": "/tmp/x.png", "direction": "horizontal"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["error"] == "flip fail"

    async def test_unexpected_exception(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        async def boom(*_args: Any, **_kwargs: Any) -> _MockResult:
            raise RuntimeError("oops")

        mock_backend.flip_hook = boom

        result = await app.call_tool(
            "flip_image",
            {"image_path": "/tmp/x.png"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "oops" in body["error"]


class TestCreateThumbnail:
    """``create_thumbnail`` forwards (width, height) tuple."""

    async def test_success(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "create_thumbnail",
            {"image_path": "/tmp/x.png", "width": 100, "height": 100},
        )
        body = _structured(result)
        assert body["success"] is True
        assert body["data"]["output_path"] == "/tmp/out.png"
        assert body["data"]["thumbnail_size"] == [50, 40]

    async def test_backend_failure(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "thumb fail"

        result = await app.call_tool(
            "create_thumbnail",
            {"image_path": "/tmp/x.png", "width": 100, "height": 100},
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["error"] == "thumb fail"

    async def test_unexpected_exception(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        async def boom(*_args: Any, **_kwargs: Any) -> _MockResult:
            raise OSError("disk full")

        mock_backend.thumbnail_hook = boom

        result = await app.call_tool(
            "create_thumbnail",
            {"image_path": "/tmp/x.png", "width": 100, "height": 100},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "disk full" in body["error"]


class TestListAvailableFilters:
    """``list_available_filters`` returns the static filter catalog."""

    async def test_returns_filter_catalog(self, app: FastMCP) -> None:
        result = await app.call_tool("list_available_filters", {})
        body = _structured(result)

        assert body["success"] is True
        assert "filters" in body["data"]
        filters = body["data"]["filters"]
        # Pin the filter set so this test catches drift
        expected_keys = {
            "blur",
            "sharpen",
            "edge_enhance",
            "emboss",
            "smooth",
            "grayscale",
            "sepia",
            "invert",
            "contrast",
            "brightness",
        }
        assert set(filters.keys()) == expected_keys
        assert body["data"]["intensity_range"] == "0.0 - 2.0 (1.0 = normal)"