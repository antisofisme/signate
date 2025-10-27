"""
Configuration Settings
Loads environment variables from .env file
"""

from typing import List, Union, Any
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field, field_validator, model_validator


class Settings(BaseSettings):
    """
    Application Settings
    All settings loaded from environment variables (.env file)
    """

    # =============================================================================
    # PROJECT INFO
    # =============================================================================
    PROJECT_NAME: str = "Smart TV Digital Signage API"
    ENVIRONMENT: str = Field(default="development", env="ENVIRONMENT")
    DEBUG: bool = Field(default=True, env="DEBUG")

    # =============================================================================
    # SERVER CONFIG
    # =============================================================================
    API_HOST: str = Field(default="0.0.0.0", env="API_HOST")
    API_PORT: int = Field(default=8000, env="API_PORT")
    API_BASE_URL: str = Field(
        default="http://localhost:8001",
        env="API_BASE_URL",
        description="External URL for API (must be configured in .env)"
    )

    # =============================================================================
    # DATABASE
    # =============================================================================
    DATABASE_URL: str = Field(
        default="postgresql://signage_user:password@postgres:5432/signage_db",
        env="DATABASE_URL",
        description="Database connection URL (must be configured in .env)"
    )

    # =============================================================================
    # REDIS
    # =============================================================================
    REDIS_URL: str = Field(
        default="redis://redis:6379",
        env="REDIS_URL",
        description="Redis connection URL (use Docker service name or host IP)"
    )

    # =============================================================================
    # ANTHIAS INTEGRATION
    # =============================================================================
    ANTHIAS_API_URL: str = Field(
        default="http://localhost:8000",
        env="ANTHIAS_API_URL",
        description="External Anthias API URL (must be configured in .env)"
    )
    ANTHIAS_INTERNAL_URL: str = Field(
        default="http://anthias-nginx",
        env="ANTHIAS_INTERNAL_URL",
        description="Internal Anthias URL for backend-to-anthias communication"
    )
    ANTHIAS_PUBLIC_URL: str = Field(
        default="http://localhost:8000",
        env="ANTHIAS_PUBLIC_URL",
        description="Public Anthias URL for client access"
    )
    ANTHIAS_API_KEY: str = Field(default="", env="ANTHIAS_API_KEY")

    # =============================================================================
    # SECURITY
    # =============================================================================
    SECRET_KEY: str = Field(
        ...,  # Required field - must be set in .env
        env="SECRET_KEY",
        description="Secret key for application (REQUIRED in .env)"
    )
    JWT_SECRET: str = Field(
        ...,  # Required field - must be set in .env
        env="JWT_SECRET",
        description="JWT secret key (REQUIRED in .env)"
    )
    JWT_ALGORITHM: str = Field(default="HS256", env="JWT_ALGORITHM")
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=15, env="JWT_ACCESS_TOKEN_EXPIRE_MINUTES")
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = Field(default=7, env="JWT_REFRESH_TOKEN_EXPIRE_DAYS")

    ENCRYPTION_KEY: str = Field(
        ...,  # Required field - must be set in .env
        env="ENCRYPTION_KEY",
        description="Encryption key for sensitive data (REQUIRED in .env)"
    )

    # =============================================================================
    # CORS
    # =============================================================================
    ENABLE_CORS: bool = Field(default=True, env="ENABLE_CORS")
    CORS_ORIGINS: Union[str, List[str]] = Field(
        default=[
            "http://localhost:3000",
            "http://localhost:8000",
            "http://localhost:8080",
        ],
        env="CORS_ORIGINS",
        description="Comma-separated list of allowed CORS origins (configure in .env)"
    )

    # =============================================================================
    # DEVELOPMENT TOOLS
    # =============================================================================
    ENABLE_API_DOCS: bool = Field(default=True, env="ENABLE_API_DOCS")
    ENABLE_HOT_RELOAD: bool = Field(default=True, env="ENABLE_HOT_RELOAD")

    # =============================================================================
    # FILE UPLOAD
    # =============================================================================
    MAX_UPLOAD_SIZE: int = Field(default=104857600, env="MAX_UPLOAD_SIZE")  # 100MB in bytes
    ALLOWED_IMAGE_TYPES: Union[str, List[str]] = Field(
        default=["image/jpeg", "image/png", "image/gif"],
        env="ALLOWED_IMAGE_TYPES"
    )
    ALLOWED_VIDEO_TYPES: Union[str, List[str]] = Field(
        default=["video/mp4", "video/mpeg", "video/quicktime"],
        env="ALLOWED_VIDEO_TYPES"
    )

    # =============================================================================
    # LOGGING
    # =============================================================================
    LOG_LEVEL: str = Field(default="INFO", env="LOG_LEVEL")
    LOG_FORMAT: str = Field(default="json", env="LOG_FORMAT")

    # =============================================================================
    # CACHE
    # =============================================================================
    CACHE_PLAYLIST_TTL: int = Field(default=300, env="CACHE_PLAYLIST_TTL")  # 5 minutes
    CACHE_GUEST_INFO_TTL: int = Field(default=300, env="CACHE_GUEST_INFO_TTL")  # 5 minutes
    CACHE_CONTENT_METADATA_TTL: int = Field(default=900, env="CACHE_CONTENT_METADATA_TTL")  # 15 minutes

    # =============================================================================
    # RATE LIMITING
    # =============================================================================
    RATE_LIMIT_PER_DEVICE: int = Field(default=60, env="RATE_LIMIT_PER_DEVICE")  # requests per minute
    RATE_LIMIT_PER_IP: int = Field(default=100, env="RATE_LIMIT_PER_IP")  # requests per minute

    # =============================================================================
    # MONITORING & HEALTH
    # =============================================================================
    HEALTH_CHECK_INTERVAL: int = Field(default=60, env="HEALTH_CHECK_INTERVAL")  # seconds
    DEVICE_HEARTBEAT_TIMEOUT: int = Field(default=300, env="DEVICE_HEARTBEAT_TIMEOUT")  # seconds

    # =============================================================================
    # FIREBIRD API (External)
    # =============================================================================
    FIREBIRD_API_URL: str = Field(default="", env="FIREBIRD_API_URL")
    FIREBIRD_API_KEY: str = Field(default="", env="FIREBIRD_API_KEY")
    FIREBIRD_REFRESH_INTERVAL: int = Field(default=300, env="FIREBIRD_REFRESH_INTERVAL")  # seconds

    # =============================================================================
    # PYDANTIC CONFIG
    # =============================================================================

    model_config = SettingsConfigDict(
        env_file='.env',
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

    # =============================================================================
    # VALIDATORS
    # =============================================================================

    @field_validator('CORS_ORIGINS', 'ALLOWED_IMAGE_TYPES', 'ALLOWED_VIDEO_TYPES', mode='before')
    @classmethod
    def parse_comma_separated_list(cls, v: Any) -> List[str]:
        """Parse comma-separated string into list"""
        if v is None:
            return []
        if isinstance(v, str):
            if not v.strip():
                return []
            return [item.strip() for item in v.split(',') if item.strip()]
        if isinstance(v, list):
            return v
        return []


# Create settings instance
settings = Settings()
