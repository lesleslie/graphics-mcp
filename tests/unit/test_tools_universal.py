"""Unit tests for ``graphics_mcp.tools.universal``.

Covers the universal-tool wrappers (get_image_info, convert_image,
list_allowed_directories, list_supported_formats) using a mock
``PillowBackend`` to avoid PIL I/O.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Any

import pytest
from fastmcp import FastMCP

from graphics_mcp.config import get_settings
from graphics_mcp.tools.universal import register_universal_tools


@dataclass
class _MockInfo:
    """Mimics ``ImageInfo`` for the mock backend."""

    path: str = "/tmp/x.png"
    width: int = 100
    height: int = 80
    format: str = "PNG"
    mode: str = "RGB"
    size_bytes: int = 1234
    has_transparency: bool = False

    def model_dump(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "width": self.width,
            "height": self.height,
            "format": self.format,
            "mode": self.mode,
            "size_bytes": self.size_bytes,
            "has_transparency": self.has_transparency,
        }


@dataclass
class _MockResult:
    success: bool
    source_path: str
    output_path: str | None = None
    message: str = ""
    original_size: tuple[int, int] | None = None
    new_size: tuple[int, int] | None = None
    error: str | None = None


class MockPillowBackend:
    """Records calls and returns canned values."""

    def __init__(self) -> None:
        self.calls: list[tuple[str, dict[str, Any]]] = []
        self.next_success: bool = True
        self.next_message: str = "ok"
        self.next_error: str | None = None
        self.next_output: str = "/tmp/out.png"
        self.next_original_size: tuple[int, int] = (100, 80)
        self.next_new_size: tuple[int, int] = (100, 80)
        self.next_info: _MockInfo = _MockInfo()
        self.raise_with: Exception | None = None

    async def get_info(self, image_path: str) -> _MockInfo:
        self.calls.append(("get_info", {"image_path": image_path}))
        if self.raise_with:
            raise self.raise_with
        return self.next_info

    async def convert(
        self, image_path: str, options: Any, output_path: str | None = None
    ) -> _MockResult:
        self.calls.append(
            ("convert", {"image_path": image_path, "options": options, "output_path": output_path})
        )
        if self.raise_with:
            raise self.raise_with
        return _MockResult(
            success=self.next_success,
            source_path=image_path,
            output_path=self.next_output if self.next_success else None,
            message=self.next_message,
            original_size=self.next_original_size,
            new_size=self.next_new_size,
            error=self.next_error,
        )


@pytest.fixture
def mock_backend() -> MockPillowBackend:
    return MockPillowBackend()


@pytest.fixture
def app(mock_backend: MockPillowBackend) -> FastMCP:
    server = FastMCP(name="TestUniversal")
    register_universal_tools(server, mock_backend)
    return server


def _structured(result: Any) -> dict[str, Any]:
    assert result.structured_content is not None, f"Missing structured_content: {result}"
    return result.structured_content  # type: ignore[no-any-return]


class TestGetImageInfo:
    """``get_image_info`` calls backend.get_info and serializes the result."""

    async def test_success_returns_info_dump(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_info = _MockInfo(
            path="/tmp/x.png",
            width=200,
            height=150,
            format="PNG",
            mode="RGBA",
            size_bytes=4096,
            has_transparency=True,
        )

        result = await app.call_tool(
            "get_image_info", {"image_path": "/tmp/x.png"}
        )
        body = _structured(result)

        assert body["success"] is True
        data = body["data"]
        assert data["width"] == 200
        assert data["height"] == 150
        assert data["format"] == "PNG"
        assert data["mode"] == "RGBA"
        assert data["has_transparency"] is True
        assert data["size_bytes"] == 4096

    async def test_file_not_found(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.raise_with = FileNotFoundError("not found")

        result = await app.call_tool(
            "get_image_info", {"image_path": "/tmp/missing.png"}
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["message"] == "Image file not found"
        assert "not found" in body["error"]

    async def test_value_error_returns_invalid_path(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.raise_with = ValueError("bad path")

        result = await app.call_tool(
            "get_image_info", {"image_path": "/tmp/x.png"}
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["message"] == "Invalid path or file"

    async def test_unexpected_exception_returns_error(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.raise_with = RuntimeError("unexpected")

        result = await app.call_tool(
            "get_image_info", {"image_path": "/tmp/x.png"}
        )
        body = _structured(result)
        assert body["success"] is False
        assert "unexpected" in body["error"]


class TestConvertImage:
    """``convert_image`` validates format string and forwards to backend."""

    async def test_success(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "convert_image",
            {
                "image_path": "/tmp/x.png",
                "output_format": "JPEG",
                "quality": 90,
                "optimize": True,
            },
        )
        body = _structured(result)

        assert body["success"] is True
        assert body["data"]["output_path"] == "/tmp/out.png"

        # Verify backend received ConvertOptions with the uppercase format
        call = mock_backend.calls[-1]
        assert call[0] == "convert"
        opts = call[1]["options"]
        assert opts.output_format.value == "JPEG"
        assert opts.quality == 90
        assert opts.optimize is True

    async def test_invalid_format(self, app: FastMCP) -> None:
        result = await app.call_tool(
            "convert_image",
            {"image_path": "/tmp/x.png", "output_format": "BOGUS"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "Invalid format" in body["message"]

    async def test_lowercase_format_normalized(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        result = await app.call_tool(
            "convert_image",
            {"image_path": "/tmp/x.png", "output_format": "png"},
        )
        body = _structured(result)
        assert body["success"] is True
        call = mock_backend.calls[-1]
        assert call[1]["options"].output_format.value == "PNG"

    async def test_backend_failure(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.next_success = False
        mock_backend.next_error = "convert boom"

        result = await app.call_tool(
            "convert_image",
            {"image_path": "/tmp/x.png", "output_format": "PNG"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert body["error"] == "convert boom"

    async def test_unexpected_exception(
        self, app: FastMCP, mock_backend: MockPillowBackend
    ) -> None:
        mock_backend.raise_with = OSError("disk full")

        result = await app.call_tool(
            "convert_image",
            {"image_path": "/tmp/x.png", "output_format": "PNG"},
        )
        body = _structured(result)
        assert body["success"] is False
        assert "disk full" in body["error"]


class TestListAllowedDirectories:
    """``list_allowed_directories`` exposes settings."""

    async def test_returns_settings_snapshot(
        self, app: FastMCP, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv(
            "GRAPHICS_ALLOWED_DIRECTORIES", json.dumps(["/tmp", "/var/tmp"])
        )
        monkeypatch.setenv("GRAPHICS_MAX_FILE_SIZE_MB", "50")
        get_settings.cache_clear()
        try:
            result = await app.call_tool("list_allowed_directories", {})
            body = _structured(result)

            assert body["success"] is True
            assert "/tmp" in body["data"]["directories"]
            assert "/var/tmp" in body["data"]["directories"]
            assert body["data"]["max_file_size_mb"] == 50
            assert "JPEG" in body["data"]["allowed_formats"]
        finally:
            get_settings.cache_clear()

    async def test_default_settings_when_env_unset(self, app: FastMCP) -> None:
        # No env override; use defaults from GraphicsSettings
        result = await app.call_tool("list_allowed_directories", {})
        body = _structured(result)

        assert body["success"] is True
        assert isinstance(body["data"]["directories"], list)
        assert body["data"]["max_file_size_mb"] == 100  # default


class TestListSupportedFormats:
    """``list_supported_formats`` returns the static format catalog."""

    async def test_returns_format_catalog(self, app: FastMCP) -> None:
        result = await app.call_tool("list_supported_formats", {})
        body = _structured(result)

        assert body["success"] is True
        formats = body["data"]["formats"]
        expected_keys = {"JPEG", "PNG", "GIF", "BMP", "WEBP", "TIFF"}
        assert set(formats.keys()) == expected_keys

        # Verify a few properties
        assert formats["PNG"]["supports_transparency"] is True
        assert formats["JPEG"]["lossy"] is True
        assert formats["GIF"]["animation"] is True
        assert formats["WEBP"]["lossy"] is True
