"""
Firebird Database Integration Models
Manages configuration for Firebird database connections
"""

from sqlalchemy import Column, Integer, String, DateTime, Boolean, Text, CheckConstraint
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base
import json
from typing import Optional, Dict, Any


class FirebirdConfig(Base):
    """
    Firebird database configuration model

    Stores connection settings and configuration for external Firebird databases.
    Supports both server and embedded connection modes.

    Attributes:
        id: Primary key
        config_key: Unique configuration identifier
        host: Server hostname/IP (NULL for embedded mode)
        port: Server port (default 3050, ignored in embedded mode)
        database_path: Full path to .fdb file
        username: Firebird username
        password: Encrypted password
        charset: Character encoding (default UTF8)
        connection_mode: 'server' or 'embedded'
        max_connections: Maximum pool size (1-20)
        connection_timeout: Connection timeout in seconds
        query_timeout: Maximum query execution time in seconds
        refresh_interval: Data refresh interval in seconds
        is_active: Whether this config is active
        last_sync: Last successful sync timestamp
        last_error: Last error message
        error_count: Cumulative error count
        last_health_check: Last health check timestamp
        config_json: Additional configuration in JSON format
        notes: Administrative notes
        created_at: Creation timestamp
        updated_at: Last update timestamp
        created_by: User who created the config
        updated_by: User who last updated the config
    """

    __tablename__ = "firebird_config"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Configuration Identifier
    config_key = Column(String(50), unique=True, nullable=False, index=True)

    # Connection Settings
    host = Column(String(255), nullable=True)  # NULL for embedded mode
    port = Column(Integer, default=3050, nullable=False)
    database_path = Column(String(500), nullable=False)
    username = Column(String(100), nullable=False)
    password = Column(String(255), nullable=False)  # Encrypted
    charset = Column(String(50), default='UTF8', nullable=False)
    connection_mode = Column(
        String(20),
        default='server',
        nullable=False,
        server_default='server'
    )

    # Connection Pool Configuration
    max_connections = Column(Integer, default=5, nullable=False)
    connection_timeout = Column(Integer, default=30, nullable=False)  # seconds
    query_timeout = Column(Integer, default=60, nullable=False)  # seconds

    # Operational Settings
    refresh_interval = Column(Integer, default=300, nullable=False)  # seconds
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Health Monitoring
    last_sync = Column(DateTime(timezone=True), nullable=True)
    last_error = Column(Text, nullable=True)
    error_count = Column(Integer, default=0, nullable=False)
    last_health_check = Column(DateTime(timezone=True), nullable=True)

    # Additional Configuration
    config_json = Column(Text, nullable=True)  # JSON string for additional settings
    notes = Column(Text, nullable=True)

    # Audit Fields
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    # Table Constraints
    __table_args__ = (
        CheckConstraint(
            "connection_mode IN ('server', 'embedded')",
            name='check_connection_mode'
        ),
        CheckConstraint(
            "max_connections BETWEEN 1 AND 20",
            name='check_max_connections'
        ),
    )

    # Relationships (if needed in future)
    # query_logs = relationship("FirebirdQueryLog", back_populates="config", cascade="all, delete-orphan")
    # cache_entries = relationship("FirebirdCache", back_populates="config", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<FirebirdConfig(id={self.id}, key='{self.config_key}', mode='{self.connection_mode}', active={self.is_active})>"

    def to_dict(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """
        Convert model to dictionary

        Args:
            include_sensitive: Whether to include sensitive data like passwords

        Returns:
            Dictionary representation of the model
        """
        data = {
            "id": self.id,
            "config_key": self.config_key,
            "host": self.host,
            "port": self.port,
            "database_path": self.database_path,
            "username": self.username,
            "charset": self.charset,
            "connection_mode": self.connection_mode,
            "max_connections": self.max_connections,
            "connection_timeout": self.connection_timeout,
            "query_timeout": self.query_timeout,
            "refresh_interval": self.refresh_interval,
            "is_active": self.is_active,
            "last_sync": self.last_sync.isoformat() if self.last_sync else None,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "last_health_check": self.last_health_check.isoformat() if self.last_health_check else None,
            "config_json": json.loads(self.config_json) if self.config_json else None,
            "notes": self.notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "created_by": self.created_by,
            "updated_by": self.updated_by
        }

        # Only include password if explicitly requested (and handle carefully)
        if include_sensitive:
            data["password"] = self.password  # Still encrypted

        return data

    def get_dsn(self) -> str:
        """
        Build DSN (Data Source Name) for Firebird connection

        Returns:
            DSN string for fdb connection
        """
        if self.connection_mode == 'embedded':
            # Embedded mode: just the database path
            return self.database_path
        else:
            # Server mode: host:port/path
            return f"{self.host}:{self.port}/{self.database_path}"

    def get_connection_params(self) -> Dict[str, Any]:
        """
        Get connection parameters for fdb.connect()

        Returns:
            Dictionary of connection parameters
        """
        params = {
            'dsn': self.get_dsn(),
            'user': self.username,
            'password': self.password,  # Should be decrypted before use
            'charset': self.charset
        }

        # Add additional parameters from config_json if present
        if self.config_json:
            try:
                extra_config = json.loads(self.config_json)
                if 'connection_params' in extra_config:
                    params.update(extra_config['connection_params'])
            except json.JSONDecodeError:
                pass

        return params

    def should_refresh(self) -> bool:
        """
        Check if data refresh is needed based on refresh_interval

        Returns:
            True if refresh is needed, False otherwise
        """
        if not self.is_active:
            return False

        if not self.last_sync:
            return True

        from datetime import datetime, timedelta
        now = datetime.now(self.last_sync.tzinfo)
        next_refresh = self.last_sync + timedelta(seconds=self.refresh_interval)

        return now >= next_refresh

    def update_health_status(self, success: bool, error_message: Optional[str] = None):
        """
        Update health monitoring fields

        Args:
            success: Whether the last operation was successful
            error_message: Error message if operation failed
        """
        from datetime import datetime

        self.last_health_check = datetime.utcnow()

        if success:
            self.last_sync = datetime.utcnow()
            self.error_count = 0  # Reset error count on success
            self.last_error = None
        else:
            self.error_count += 1
            if error_message:
                self.last_error = error_message

    def get_config_value(self, key: str, default: Any = None) -> Any:
        """
        Get a value from config_json

        Args:
            key: Configuration key
            default: Default value if key not found

        Returns:
            Configuration value or default
        """
        if not self.config_json:
            return default

        try:
            config = json.loads(self.config_json)
            return config.get(key, default)
        except json.JSONDecodeError:
            return default

    def set_config_value(self, key: str, value: Any):
        """
        Set a value in config_json

        Args:
            key: Configuration key
            value: Configuration value
        """
        try:
            config = json.loads(self.config_json) if self.config_json else {}
        except json.JSONDecodeError:
            config = {}

        config[key] = value
        self.config_json = json.dumps(config)


class FirebirdQueryLog(Base):
    """
    Audit log for Firebird query execution

    Tracks all queries executed against Firebird databases
    for security auditing and performance monitoring.
    """

    __tablename__ = "firebird_query_log"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Reference to configuration
    config_id = Column(Integer, nullable=False, index=True)

    # Query Information
    query_text = Column(Text, nullable=False)
    query_hash = Column(String(64), nullable=True, index=True)
    execution_time_ms = Column(Integer, nullable=True)
    row_count = Column(Integer, nullable=True)

    # Execution Status
    success = Column(Boolean, default=True, nullable=False, index=True)
    error_message = Column(Text, nullable=True)
    error_code = Column(String(20), nullable=True)

    # Context Information
    executed_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    executed_by = Column(String(100), nullable=True, index=True)
    request_id = Column(String(50), nullable=True)
    ip_address = Column(String(45), nullable=True)

    # Performance Metrics
    bytes_sent = Column(Integer, nullable=True)
    bytes_received = Column(Integer, nullable=True)

    def __repr__(self):
        return f"<FirebirdQueryLog(id={self.id}, config_id={self.config_id}, success={self.success})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "config_id": self.config_id,
            "query_text": self.query_text[:100] + "..." if len(self.query_text) > 100 else self.query_text,
            "query_hash": self.query_hash,
            "execution_time_ms": self.execution_time_ms,
            "row_count": self.row_count,
            "success": self.success,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "executed_at": self.executed_at.isoformat() if self.executed_at else None,
            "executed_by": self.executed_by,
            "request_id": self.request_id,
            "ip_address": self.ip_address
        }


class FirebirdCache(Base):
    """
    Cache for Firebird query results

    Stores cached query results for performance optimization.
    """

    __tablename__ = "firebird_cache"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Cache Key
    cache_key = Column(String(255), unique=True, nullable=False, index=True)
    config_id = Column(Integer, nullable=False, index=True)

    # Cached Data
    query_hash = Column(String(64), nullable=False)
    result_data = Column(Text, nullable=False)  # JSON serialized
    result_count = Column(Integer, nullable=True)

    # Cache Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    hit_count = Column(Integer, default=0, nullable=False)
    last_accessed = Column(DateTime(timezone=True), nullable=True)

    # Cache Configuration
    ttl_seconds = Column(Integer, default=300, nullable=False)
    is_valid = Column(Boolean, default=True, nullable=False, index=True)

    def __repr__(self):
        return f"<FirebirdCache(id={self.id}, key='{self.cache_key}', valid={self.is_valid})>"

    def is_expired(self) -> bool:
        """Check if cache entry has expired"""
        from datetime import datetime
        return datetime.utcnow() >= self.expires_at

    def increment_hit_count(self):
        """Increment hit count and update last accessed time"""
        from datetime import datetime
        self.hit_count += 1
        self.last_accessed = datetime.utcnow()


class FirebirdQueryTemplate(Base):
    """
    Predefined query templates for common operations

    Stores reusable query templates with parameter placeholders.
    """

    __tablename__ = "firebird_query_templates"

    # Primary Key
    id = Column(Integer, primary_key=True, index=True)

    # Template Identification
    template_key = Column(String(100), unique=True, nullable=False, index=True)
    template_name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)

    # Query Definition
    query_template = Column(Text, nullable=False)
    parameter_schema = Column(Text, nullable=True)  # JSON schema

    # Configuration
    config_id = Column(Integer, nullable=True, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    cache_ttl = Column(Integer, default=300, nullable=False)
    max_rows = Column(Integer, default=1000, nullable=False)

    # Usage Tracking
    usage_count = Column(Integer, default=0, nullable=False)
    last_used = Column(DateTime(timezone=True), nullable=True)

    # Metadata
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)
    created_by = Column(String(100), nullable=True)
    updated_by = Column(String(100), nullable=True)

    def __repr__(self):
        return f"<FirebirdQueryTemplate(id={self.id}, key='{self.template_key}', active={self.is_active})>"

    def to_dict(self) -> Dict[str, Any]:
        """Convert model to dictionary"""
        return {
            "id": self.id,
            "template_key": self.template_key,
            "template_name": self.template_name,
            "description": self.description,
            "query_template": self.query_template,
            "parameter_schema": json.loads(self.parameter_schema) if self.parameter_schema else None,
            "config_id": self.config_id,
            "is_active": self.is_active,
            "cache_ttl": self.cache_ttl,
            "max_rows": self.max_rows,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

    def increment_usage(self):
        """Increment usage count and update last used time"""
        from datetime import datetime
        self.usage_count += 1
        self.last_used = datetime.utcnow()