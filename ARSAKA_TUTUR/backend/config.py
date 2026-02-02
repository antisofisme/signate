"""
Configuration management for ARSAKA_TUTUR.

Loads settings from environment variables with defaults.
"""

import os
from dataclasses import dataclass, field
from typing import Optional
from functools import lru_cache


@dataclass
class DatabaseConfig:
    """PostgreSQL configuration."""
    host: str = "localhost"
    port: int = 5432
    database: str = "arsaka_tutur"
    user: str = "chat"
    password: str = ""
    min_connections: int = 5
    max_connections: int = 20

    @property
    def dsn(self) -> str:
        """Get connection DSN."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

    @classmethod
    def from_env(cls) -> "DatabaseConfig":
        """Load from environment."""
        # Support DATABASE_URL or individual settings
        database_url = os.getenv("DATABASE_URL")
        if database_url:
            # Parse postgresql://user:pass@host:port/db
            from urllib.parse import urlparse
            parsed = urlparse(database_url)
            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 5432,
                database=parsed.path.lstrip("/") if parsed.path else "arsaka_tutur",
                user=parsed.username or "chat",
                password=parsed.password or "",
            )
        return cls(
            host=os.getenv("DB_HOST", "localhost"),
            port=int(os.getenv("DB_PORT", "5432")),
            database=os.getenv("DB_NAME", "arsaka_tutur"),
            user=os.getenv("DB_USER", "chat"),
            password=os.getenv("DB_PASSWORD", ""),
            min_connections=int(os.getenv("DB_MIN_CONN", "5")),
            max_connections=int(os.getenv("DB_MAX_CONN", "20")),
        )


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None

    @property
    def url(self) -> str:
        """Get connection URL."""
        auth = f":{self.password}@" if self.password else ""
        return f"redis://{auth}{self.host}:{self.port}/{self.db}"

    @classmethod
    def from_env(cls) -> "RedisConfig":
        """Load from environment."""
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            from urllib.parse import urlparse
            parsed = urlparse(redis_url)
            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 6379,
                db=int(parsed.path.lstrip("/") or "0"),
                password=parsed.password,
            )
        return cls(
            host=os.getenv("REDIS_HOST", "localhost"),
            port=int(os.getenv("REDIS_PORT", "6379")),
            db=int(os.getenv("REDIS_DB", "0")),
            password=os.getenv("REDIS_PASSWORD"),
        )


@dataclass
class QdrantConfig:
    """Qdrant vector database configuration."""
    host: str = "localhost"
    port: int = 6333
    grpc_port: int = 6334
    api_key: Optional[str] = None
    prefer_grpc: bool = False

    @property
    def url(self) -> str:
        """Get connection URL."""
        return f"http://{self.host}:{self.port}"

    @classmethod
    def from_env(cls) -> "QdrantConfig":
        """Load from environment."""
        qdrant_url = os.getenv("QDRANT_URL")
        if qdrant_url:
            from urllib.parse import urlparse
            parsed = urlparse(qdrant_url)
            return cls(
                host=parsed.hostname or "localhost",
                port=parsed.port or 6333,
                api_key=os.getenv("QDRANT_API_KEY"),
            )
        return cls(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333")),
            grpc_port=int(os.getenv("QDRANT_GRPC_PORT", "6334")),
            api_key=os.getenv("QDRANT_API_KEY"),
            prefer_grpc=os.getenv("QDRANT_PREFER_GRPC", "false").lower() == "true",
        )


@dataclass
class OpenAIConfig:
    """OpenAI API configuration."""
    api_key: str = ""
    organization: Optional[str] = None
    default_model: str = "gpt-4o-mini"
    embedding_model: str = "text-embedding-3-small"
    embedding_dimensions: int = 1536

    @classmethod
    def from_env(cls) -> "OpenAIConfig":
        """Load from environment."""
        return cls(
            api_key=os.getenv("OPENAI_API_KEY", ""),
            organization=os.getenv("OPENAI_ORGANIZATION"),
            default_model=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
            embedding_model=os.getenv("OPENAI_EMBEDDING_MODEL", "text-embedding-3-small"),
            embedding_dimensions=int(os.getenv("OPENAI_EMBEDDING_DIMENSIONS", "1536")),
        )


@dataclass
class JWTConfig:
    """JWT authentication configuration."""
    secret_key: str = ""
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    refresh_token_expire_days: int = 7

    @classmethod
    def from_env(cls) -> "JWTConfig":
        """Load from environment."""
        return cls(
            secret_key=os.getenv("JWT_SECRET_KEY", "change-me-in-production"),
            algorithm=os.getenv("JWT_ALGORITHM", "HS256"),
            access_token_expire_minutes=int(os.getenv("JWT_ACCESS_EXPIRE_MINUTES", "60")),
            refresh_token_expire_days=int(os.getenv("JWT_REFRESH_EXPIRE_DAYS", "7")),
        )


@dataclass
class RateLimitConfig:
    """Rate limiting configuration."""
    enabled: bool = True
    chat_per_minute: int = 30
    search_per_minute: int = 60
    general_per_minute: int = 120
    admin_per_minute: int = 10

    @classmethod
    def from_env(cls) -> "RateLimitConfig":
        """Load from environment."""
        return cls(
            enabled=os.getenv("RATE_LIMIT_ENABLED", "true").lower() == "true",
            chat_per_minute=int(os.getenv("RATE_LIMIT_CHAT", "30")),
            search_per_minute=int(os.getenv("RATE_LIMIT_SEARCH", "60")),
            general_per_minute=int(os.getenv("RATE_LIMIT_GENERAL", "120")),
            admin_per_minute=int(os.getenv("RATE_LIMIT_ADMIN", "10")),
        )


@dataclass
class Settings:
    """
    Application settings.

    All configuration is loaded from environment variables.
    """
    # App info
    app_name: str = "ARSAKA_TUTUR"
    app_version: str = "1.0.0"
    environment: str = "development"
    debug: bool = False

    # Server
    host: str = "0.0.0.0"
    port: int = 8003

    # CORS
    cors_origins: list = field(default_factory=lambda: ["*"])

    # Components
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    qdrant: QdrantConfig = field(default_factory=QdrantConfig)
    openai: OpenAIConfig = field(default_factory=OpenAIConfig)
    jwt: JWTConfig = field(default_factory=JWTConfig)
    rate_limit: RateLimitConfig = field(default_factory=RateLimitConfig)

    # Logging
    log_level: str = "INFO"
    log_format: str = "json"

    @classmethod
    def from_env(cls) -> "Settings":
        """Load all settings from environment."""
        cors_origins = os.getenv("CORS_ORIGINS", "*").split(",")

        return cls(
            app_name=os.getenv("APP_NAME", "ARSAKA_TUTUR"),
            app_version=os.getenv("APP_VERSION", "1.0.0"),
            environment=os.getenv("ENVIRONMENT", "development"),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            host=os.getenv("HOST", "0.0.0.0"),
            port=int(os.getenv("PORT", "8003")),
            cors_origins=cors_origins,
            database=DatabaseConfig.from_env(),
            redis=RedisConfig.from_env(),
            qdrant=QdrantConfig.from_env(),
            openai=OpenAIConfig.from_env(),
            jwt=JWTConfig.from_env(),
            rate_limit=RateLimitConfig.from_env(),
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            log_format=os.getenv("LOG_FORMAT", "json"),
        )

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development."""
        return self.environment == "development"

    @property
    def jwt_secret(self) -> str:
        """Get JWT secret key."""
        return self.jwt.secret_key

    @property
    def rate_limit_per_minute(self) -> int:
        """Get general rate limit per minute."""
        return self.rate_limit.general_per_minute


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.

    Use this function to get settings throughout the app.
    """
    return Settings.from_env()
