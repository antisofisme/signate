"""
Runtime Configuration

Environment-based configuration for ATLAS_MANTRA backend.
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class Config:
    """Application configuration."""

    # Database
    database_url: str = os.getenv(
        "DATABASE_URL",
        "postgresql://mantra:mantra@localhost:5432/atlas_mantra"
    )

    # Server
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))

    # API
    api_prefix: str = os.getenv("API_PREFIX", "/api/v1")

    # Logging
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # CORS
    cors_origins: str = os.getenv(
        "CORS_ORIGINS",
        "http://localhost:3000,http://localhost:5173"
    )

    # Feature flags
    enable_docs: bool = os.getenv("ENABLE_DOCS", "true").lower() == "true"
    enable_metrics: bool = os.getenv("ENABLE_METRICS", "false").lower() == "true"

    @property
    def cors_origins_list(self) -> list[str]:
        """Parse CORS origins as list."""
        return [o.strip() for o in self.cors_origins.split(",") if o.strip()]


def get_config() -> Config:
    """Get configuration instance."""
    return Config()
