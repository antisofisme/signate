"""
SHARED CONFIGURATION
Loaded from .env file (root level)
"""

from pydantic_settings import BaseSettings
from pydantic import ConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings from environment variables"""

    # Environment
    ENVIRONMENT: str = "development"
    DEBUG: bool = True

    # Database
    DATABASE_URL: str

    # Redis
    REDIS_URL: str
    USE_REDIS_PUBSUB: bool = True  # Use Redis for WebSocket pub/sub (recommended for production)

    # Security
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # CORS
    ENABLE_CORS: bool = True
    CORS_ORIGINS: str = ""  # Will be parsed to list in __init__

    # API Docs
    ENABLE_API_DOCS: bool = True

    # Service Ports
    AUTH_SERVICE_PORT: int = 8001
    TENANT_SERVICE_PORT: int = 8002
    DEVICE_SERVICE_PORT: int = 8003
    CONTENT_SERVICE_PORT: int = 8004
    ANALYTICS_SERVICE_PORT: int = 8005

    # Celery
    CELERY_BROKER_URL: str = ""
    CELERY_RESULT_BACKEND: str = ""

    # File Storage
    UPLOAD_DIR: str = "/app/uploads"
    MAX_UPLOAD_SIZE: int = 524288000  # 500MB

    # External Services
    ANTHIAS_API_URL: str = ""

    # Logging
    LOG_LEVEL: str = "INFO"

    model_config = ConfigDict(
        env_file=".env",
        case_sensitive=True,
        extra="ignore"  # Ignore unknown env vars (prevents errors)
    )

    def get_cors_origins_list(self) -> List[str]:
        """Parse CORS_ORIGINS string to list"""
        if not self.CORS_ORIGINS:
            return []
        return [origin.strip() for origin in self.CORS_ORIGINS.split(',') if origin.strip()]


# Global settings instance
settings = Settings()
