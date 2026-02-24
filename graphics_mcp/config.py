"""Configuration for graphics-mcp using Oneiric patterns."""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Any

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Oneiric logging imports
try:
    from oneiric.core.logging import LoggingConfig, configure_logging, get_logger

    ONEIRIC_LOGGING_AVAILABLE = True
except ImportError:
    ONEIRIC_LOGGING_AVAILABLE = False
    import logging

    def get_logger(name: str) -> logging.Logger:
        return logging.getLogger(name)

    def configure_logging(*args: Any, **kwargs: Any) -> None:
        logging.basicConfig(level=logging.INFO)


class GraphicsSettings(BaseSettings):
    """Graphics MCP server configuration."""

    model_config = SettingsConfigDict(
        env_prefix="GRAPHICS_",
        env_file=(".env",),
        extra="ignore",
        case_sensitive=False,
    )

    # Server identification
    server_name: str = Field(
        default="graphics-mcp",
        description="Server name for identification",
    )
    server_description: str = Field(
        default="Unified MCP server for graphics manipulation",
        description="Server description",
    )

    # Backend configuration
    default_backend: str = Field(
        default="pillow",
        description="Default graphics backend (pillow, imagemagick, gimp)",
    )
    enable_pillow: bool = Field(
        default=True,
        description="Enable Pillow backend",
    )
    enable_imagemagick: bool = Field(
        default=False,
        description="Enable ImageMagick CLI backend",
    )
    enable_gimp: bool = Field(
        default=False,
        description="Enable GIMP D-Bus/HTTP backend",
    )

    # Security configuration
    allowed_directories: list[str] = Field(
        default=["/tmp", "~/Pictures", "~/Downloads"],
        description="Directories allowed for file operations",
    )
    max_file_size_mb: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum file size in MB",
    )
    allowed_formats: list[str] = Field(
        default=["JPEG", "PNG", "GIF", "BMP", "WEBP", "TIFF"],
        description="Allowed image formats",
    )

    # HTTP transport
    enable_http_transport: bool = Field(
        default=False,
        description="Enable HTTP transport",
    )
    http_host: str = Field(
        default="127.0.0.1",
        description="HTTP server host",
    )
    http_port: int = Field(
        default=3040,
        ge=1024,
        le=65535,
        description="HTTP server port",
    )

    # Logging configuration
    log_level: str = Field(
        default="INFO",
        description="Logging level",
    )
    log_json: bool = Field(
        default=True,
        description="Use JSON logging format",
    )

    @field_validator("allowed_directories", mode="before")
    @classmethod
    def expand_directories(cls, v: list[str]) -> list[str]:
        """Expand ~ in directory paths."""
        return [str(Path(p).expanduser()) for p in v]

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid:
            raise ValueError(f"Invalid log level: {v}. Must be one of {valid}")
        return v.upper()


@lru_cache
def get_settings() -> GraphicsSettings:
    """Get cached settings instance."""
    return GraphicsSettings()


def setup_logging(settings: GraphicsSettings | None = None) -> None:
    """Configure logging using Oneiric patterns."""
    if settings is None:
        settings = get_settings()

    if ONEIRIC_LOGGING_AVAILABLE:
        config = LoggingConfig(
            level=settings.log_level,
            emit_json=settings.log_json,
            service_name="graphics-mcp",
        )
        configure_logging(config)
    else:
        # Fallback to standard logging
        import logging
        logging.basicConfig(
            level=getattr(logging, settings.log_level.upper(), logging.INFO),
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        )


def get_logger_instance(name: str = "graphics-mcp") -> Any:
    """Get a structured logger instance."""
    if ONEIRIC_LOGGING_AVAILABLE:
        return get_logger(name)
    import logging
    return logging.getLogger(name)


__all__ = [
    "GraphicsSettings",
    "get_settings",
    "setup_logging",
    "get_logger_instance",
    "ONEIRIC_LOGGING_AVAILABLE",
]
