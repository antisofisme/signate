"""
Firebird schemas for request/response validation
Pydantic models for Firebird database integration
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List, Dict, Any
from datetime import datetime


class FirebirdConfigBase(BaseModel):
    """Base schema for Firebird configuration"""
    config_key: str = Field(
        ...,
        min_length=1,
        max_length=50,
        description="Unique configuration key identifier"
    )
    api_endpoint: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Firebird DSN (e.g., 'localhost:3050/path/to/db.gdb' or '/path/to/embedded.fdb')"
    )
    api_key: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Authentication credentials in format 'username:password'"
    )
    refresh_interval: int = Field(
        default=300,
        ge=10,
        le=3600,
        description="Data refresh interval in seconds (10-3600)"
    )
    is_active: bool = Field(
        default=True,
        description="Whether this configuration is active"
    )
    notes: Optional[str] = Field(
        None,
        max_length=1000,
        description="Admin notes about this integration"
    )

    @field_validator('api_key')
    @classmethod
    def validate_api_key_format(cls, v: str) -> str:
        """Validate API key format (username:password)"""
        if ':' not in v:
            raise ValueError("api_key must be in format 'username:password'")
        parts = v.split(':', 1)
        if len(parts) != 2 or not parts[0] or not parts[1]:
            raise ValueError("api_key must contain both username and password")
        return v

    @field_validator('api_endpoint')
    @classmethod
    def validate_api_endpoint(cls, v: str) -> str:
        """Validate Firebird DSN format"""
        # Basic validation - either has : for server mode or is a path
        if ':' in v:
            # Server mode: host:port/path
            parts = v.split(':', 1)
            if len(parts) != 2:
                raise ValueError("Invalid server DSN format. Expected 'host:port/path'")
        else:
            # Embedded mode: just path
            if not v.endswith(('.fdb', '.gdb', '.FDB', '.GDB')):
                raise ValueError("Database file must end with .fdb or .gdb")
        return v


class FirebirdConfigCreate(FirebirdConfigBase):
    """Schema for creating a new Firebird configuration"""

    class Config:
        json_schema_extra = {
            "example": {
                "config_key": "hotel_pms",
                "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
                "api_key": "SYSDBA:masterkey",
                "refresh_interval": 300,
                "is_active": True,
                "notes": "Hotel PMS database connection"
            }
        }


class FirebirdConfigUpdate(BaseModel):
    """Schema for updating a Firebird configuration"""
    config_key: Optional[str] = Field(None, min_length=1, max_length=50)
    api_endpoint: Optional[str] = Field(None, min_length=1, max_length=500)
    api_key: Optional[str] = Field(None, min_length=1, max_length=255)
    refresh_interval: Optional[int] = Field(None, ge=10, le=3600)
    is_active: Optional[bool] = None
    notes: Optional[str] = Field(None, max_length=1000)

    @field_validator('api_key')
    @classmethod
    def validate_api_key_format(cls, v: Optional[str]) -> Optional[str]:
        """Validate API key format (username:password)"""
        if v is not None:
            if ':' not in v:
                raise ValueError("api_key must be in format 'username:password'")
            parts = v.split(':', 1)
            if len(parts) != 2 or not parts[0] or not parts[1]:
                raise ValueError("api_key must contain both username and password")
        return v

    @field_validator('api_endpoint')
    @classmethod
    def validate_api_endpoint(cls, v: Optional[str]) -> Optional[str]:
        """Validate Firebird DSN format"""
        if v is not None:
            if ':' in v:
                parts = v.split(':', 1)
                if len(parts) != 2:
                    raise ValueError("Invalid server DSN format. Expected 'host:port/path'")
            else:
                if not v.endswith(('.fdb', '.gdb', '.FDB', '.GDB')):
                    raise ValueError("Database file must end with .fdb or .gdb")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "config_key": "hotel_pms_updated",
                "refresh_interval": 600,
                "is_active": False,
                "notes": "Temporarily disabled for maintenance"
            }
        }


class FirebirdConfigResponse(BaseModel):
    """Schema for Firebird configuration response"""
    id: int
    config_key: str
    api_endpoint: str
    refresh_interval: int
    is_active: bool
    last_sync: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_schema_extra = {
            "example": {
                "id": 1,
                "config_key": "hotel_pms",
                "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
                "refresh_interval": 300,
                "is_active": True,
                "last_sync": "2025-10-27T10:30:00",
                "notes": "Hotel PMS database connection",
                "created_at": "2025-10-27T09:00:00",
                "updated_at": "2025-10-27T10:30:00"
            }
        }


class FirebirdConfigListResponse(BaseModel):
    """Schema for list of Firebird configurations"""
    total: int
    configs: List[FirebirdConfigResponse]

    class Config:
        json_schema_extra = {
            "example": {
                "total": 2,
                "configs": [
                    {
                        "id": 1,
                        "config_key": "hotel_pms",
                        "api_endpoint": "192.168.1.100:3050/opt/databases/powerfo.gdb",
                        "refresh_interval": 300,
                        "is_active": True
                    }
                ]
            }
        }


class FirebirdTestRequest(BaseModel):
    """Schema for testing Firebird connection"""
    test_query: Optional[str] = Field(
        None,
        max_length=500,
        description="Optional test query (default: 'SELECT 1 FROM RDB$DATABASE')"
    )

    @field_validator('test_query')
    @classmethod
    def validate_test_query(cls, v: Optional[str]) -> Optional[str]:
        """Validate that test query is SELECT only"""
        if v is not None:
            # Convert to uppercase for checking
            query_upper = v.strip().upper()
            if not query_upper.startswith('SELECT'):
                raise ValueError("Only SELECT queries are allowed")
            # Check for forbidden keywords
            forbidden = ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXECUTE']
            for keyword in forbidden:
                if keyword in query_upper:
                    raise ValueError(f"Query contains forbidden keyword: {keyword}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "test_query": "SELECT FIRST 1 * FROM RDB$DATABASE"
            }
        }


class FirebirdTestResult(BaseModel):
    """Schema for Firebird connection test result"""
    success: bool
    message: str
    connection_time_ms: Optional[float] = None
    test_query_executed: Optional[bool] = None
    error_details: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "message": "Connection successful",
                "connection_time_ms": 45.2,
                "test_query_executed": True,
                "error_details": None
            }
        }


class FirebirdQueryRequest(BaseModel):
    """Schema for executing Firebird query"""
    query: str = Field(
        ...,
        min_length=1,
        max_length=5000,
        description="SQL SELECT query to execute"
    )
    max_rows: int = Field(
        default=100,
        ge=1,
        le=1000,
        description="Maximum number of rows to return (1-1000)"
    )

    @field_validator('query')
    @classmethod
    def validate_query_is_select(cls, v: str) -> str:
        """Validate that query is SELECT only (read-only)"""
        query_upper = v.strip().upper()

        # Must start with SELECT
        if not query_upper.startswith('SELECT'):
            raise ValueError("Only SELECT queries are allowed")

        # Check for forbidden keywords (DML/DDL operations)
        forbidden = [
            'INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER',
            'EXECUTE', 'GRANT', 'REVOKE', 'TRUNCATE', 'PROCEDURE',
            'TRIGGER', 'COMMIT', 'ROLLBACK'
        ]

        for keyword in forbidden:
            # Use word boundaries to avoid false positives
            if f' {keyword} ' in f' {query_upper} ' or query_upper.endswith(f' {keyword}'):
                raise ValueError(f"Query contains forbidden keyword: {keyword}")

        return v

    class Config:
        json_schema_extra = {
            "example": {
                "query": "SELECT * FROM GUESTS WHERE CHECK_IN_DATE = CURRENT_DATE",
                "max_rows": 50
            }
        }


class FirebirdQueryResult(BaseModel):
    """Schema for Firebird query execution result"""
    success: bool
    row_count: int
    columns: List[str]
    rows: List[Dict[str, Any]]
    execution_time_ms: float
    message: str
    error_details: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "row_count": 3,
                "columns": ["GUEST_ID", "GUEST_NAME", "ROOM_NUMBER", "CHECK_IN_DATE"],
                "rows": [
                    {
                        "GUEST_ID": 101,
                        "GUEST_NAME": "John Doe",
                        "ROOM_NUMBER": "205",
                        "CHECK_IN_DATE": "2025-10-27"
                    },
                    {
                        "GUEST_ID": 102,
                        "GUEST_NAME": "Jane Smith",
                        "ROOM_NUMBER": "312",
                        "CHECK_IN_DATE": "2025-10-27"
                    }
                ],
                "execution_time_ms": 23.5,
                "message": "Query executed successfully",
                "error_details": None
            }
        }


class FirebirdHealthResult(BaseModel):
    """Schema for Firebird connection health check"""
    config_id: int
    config_key: str
    is_healthy: bool
    connection_status: str  # "connected", "disconnected", "error"
    pool_status: Optional[Dict[str, Any]] = None
    last_check: datetime
    error_message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "config_id": 1,
                "config_key": "hotel_pms",
                "is_healthy": True,
                "connection_status": "connected",
                "pool_status": {
                    "total_connections": 5,
                    "available_connections": 3,
                    "active_connections": 2
                },
                "last_check": "2025-10-27T10:35:00",
                "error_message": None
            }
        }
