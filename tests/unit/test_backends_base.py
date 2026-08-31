"""Unit tests for ``graphics_mcp.backends.base``.

Covers the helper methods (``_validate_path``, ``_generate_output_path``,
``_check_file_size``) shared by every concrete backend. These are
side-effect-free aside from filesystem stat, so we exercise them against
``tmp_path`` instead of mocking.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from graphics_mcp.backends.base import BaseGraphicsBackend


class _StubBackend(BaseGraphicsBackend):
    """Minimal concrete subclass that satisfies the ABC for testing helpers."""

    @property
    def name(self) -> str:
        return "stub"

    @property
    def is_available(self) -> bool:
        return True


@pytest.fixture
def backend() -> _StubBackend:
    return _StubBackend()


class TestValidatePath:
    """``_validate_path`` resolves the path and rejects paths outside allowlist."""

    def test_returns_resolved_path_within_allowed(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        allowed = [str(tmp_path)]
        nested = tmp_path / "sub" / "image.png"
        nested.parent.mkdir()

        result = backend._validate_path(str(nested), allowed)

        assert result == nested.resolve()
        assert isinstance(result, Path)

    def test_expands_user_tilde(
        self, backend: _StubBackend, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        monkeypatch.setenv("HOME", str(tmp_path))
        target = tmp_path / "x.png"
        result = backend._validate_path("~/x.png", [str(tmp_path)])

        assert result == target.resolve()

    def test_raises_when_path_not_in_allowed(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        outside = tmp_path.parent / "elsewhere.png"

        with pytest.raises(ValueError, match="not within allowed directories"):
            backend._validate_path(str(outside), [str(tmp_path)])

    def test_raises_with_all_allowed_dirs_listed(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        allowed = [str(tmp_path / "a"), str(tmp_path / "b")]
        outside = tmp_path / "elsewhere.png"

        with pytest.raises(ValueError) as exc:
            backend._validate_path(str(outside), allowed)

        # Verify all allowed dirs are surfaced in the error message
        assert str(tmp_path / "a") in str(exc.value)
        assert str(tmp_path / "b") in str(exc.value)


class TestGenerateOutputPath:
    """``_generate_output_path`` rewrites the stem with suffix + extension."""

    def test_preserves_extension_when_no_new_format(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        src = str(tmp_path / "photo.png")

        result = backend._generate_output_path(src)

        assert result == str(tmp_path / "photo.png")

    def test_appends_suffix_to_stem(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        src = str(tmp_path / "photo.png")

        result = backend._generate_output_path(src, suffix="resized")

        assert result == str(tmp_path / "photo_resized.png")

    def test_replaces_extension_when_new_format(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        src = str(tmp_path / "photo.png")

        result = backend._generate_output_path(src, suffix="", new_format="JPEG")

        # The implementation lowercases the format string verbatim (.jpeg, not .jpg)
        assert result == str(tmp_path / "photo.jpeg")

    def test_suffix_and_new_format_combined(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        src = str(tmp_path / "photo.png")

        result = backend._generate_output_path(
            src, suffix="converted", new_format="WEBP"
        )

        assert result == str(tmp_path / "photo_converted.webp")


class TestCheckFileSize:
    """``_check_file_size`` enforces ``max_mb`` against an on-disk file."""

    def test_passes_when_under_limit(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        small = tmp_path / "small.bin"
        small.write_bytes(b"x" * 1024)  # 1 KB

        # Should not raise
        backend._check_file_size(str(small), max_mb=1)

    def test_passes_when_exactly_at_limit(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        # 1 MB file against 1 MB limit - boundary inclusive
        one_mb = tmp_path / "exact.bin"
        one_mb.write_bytes(b"x" * (1024 * 1024))

        backend._check_file_size(str(one_mb), max_mb=1)

    def test_raises_when_over_limit(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        big = tmp_path / "big.bin"
        # 2 MB file against 1 MB limit
        big.write_bytes(b"x" * (2 * 1024 * 1024))

        with pytest.raises(ValueError, match="exceeds maximum"):
            backend._check_file_size(str(big), max_mb=1)

    def test_raises_when_file_missing(
        self, backend: _StubBackend, tmp_path: Path
    ) -> None:
        missing = tmp_path / "ghost.bin"

        with pytest.raises(FileNotFoundError, match="Image not found"):
            backend._check_file_size(str(missing), max_mb=100)


class TestConstructor:
    """``BaseGraphicsBackend.__init__`` accepts an optional config dict."""

    def test_default_config_is_empty_dict(self) -> None:
        backend = _StubBackend()

        assert backend.config == {}

    def test_config_stored_when_provided(self) -> None:
        backend = _StubBackend({"key": "value"})

        assert backend.config == {"key": "value"}

    def test_explicit_none_falls_back_to_empty_dict(self) -> None:
        backend = _StubBackend(None)

        assert backend.config == {}