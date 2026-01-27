"""
ATLAS_PANDAWA Backend - Configuration
Follows CORE-STD-01 standards
"""

from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    """Application configuration settings"""

    # Application
    APP_NAME: str = "ATLAS_PANDAWA"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = False

    # Server
    HOST: str = "0.0.0.0"
    PORT: int = 8000

    # Database
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/pandawa_db"

    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"

    # JWT
    JWT_SECRET_KEY: str = "change-this-secret-key-in-production"
    JWT_ALGORITHM: str = "HS256"
    JWT_ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    JWT_REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # CORS
    CORS_ORIGINS: list[str] = ["http://localhost:3000", "http://localhost:5173"]

    # Multi-tenancy (CORE-STD-07)
    REQUIRE_TENANT_ID: bool = True

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
